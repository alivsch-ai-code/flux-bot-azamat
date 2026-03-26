import json
import os
import random
import re
import time
import threading
import logging
from datetime import datetime

import feedparser

from telebot import types

from src.presentation.telegram.handlers.gen.chat_sessions import append_global_chat_event
from src.utils.strings import get_random_daily_fallback, get_text

logger = logging.getLogger(__name__)

# Multi-RSS für AI-Themen (inkl. OpenAI Blog)
DEFAULT_AI_NEWS_RSS_URLS = [
    "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en",
    "https://openai.com/blog/rss.xml",
]


def _parse_rss_urls() -> list[str]:
    raw = (os.getenv("AI_NEWS_RSS_URLS") or "").strip()
    if raw:
        urls = [u.strip() for u in raw.split(",") if u.strip()]
        if urls:
            return urls
    # Backward compatibility: altes Einzel-Env behalten
    single = (os.getenv("AI_NEWS_RSS_URL") or "").strip()
    if single:
        return [single]
    return DEFAULT_AI_NEWS_RSS_URLS


AI_NEWS_RSS_URLS = _parse_rss_urls()

# Fallback nur 1× pro Tag senden, wenn keine DB-Nachricht
_last_fallback_date = None
_last_errors_cleanup_date = None
# Azamat-Begrüßung: bereits gesendete Slots (date, slot)
_last_azamat_slots_done = set()

AZAMAT_GREETING_MODEL = "google-gemini-2-5-flash"
RSS_WATCH_MIN_INTERVAL_SECONDS = max(300, int(os.getenv("RSS_WATCH_MIN_INTERVAL_SECONDS", "7200")))


def _resolve_daily_message_text(raw: str | None, lang: str) -> str:
    """
    Ein Post kann ein einfacher String sein oder JSON mit Sprachschlüsseln:
    {"de":"...", "en":"...", "ru":"...", "kk":"..."} → passender Text pro User.
    """
    raw = (raw or "").strip()
    if not raw:
        return ""
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                for key in (lang, "en", "de", "ru", "kk"):
                    val = data.get(key)
                    if val is not None and str(val).strip():
                        return str(val).strip()
                for val in data.values():
                    if val is not None and str(val).strip():
                        return str(val).strip()
        except json.JSONDecodeError:
            pass
    return raw


class DailyService:
    def __init__(self, bot, db, generation_service=None):
        self.bot = bot
        self.db = db
        self.generation_service = generation_service
        self.running = False

    def start(self):
        """Startet den Hintergrund-Service in einem separaten Thread."""
        self.running = True
        thread = threading.Thread(target=self._loop)
        thread.daemon = True # Thread stirbt automatisch, wenn Hauptprogramm beendet wird
        thread.start()
        logger.info("Daily Service gestartet.")

    def _loop(self):
        """
        Endlosschleife, die prüft, ob heute eine Nachricht gesendet werden muss.
        """
        while self.running:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                # 1. Prüfen: Gibt es für HEUTE einen Post, der noch NICHT gesendet wurde?
                # Die Datenbank-Methode 'get_due_daily_post' sucht nach:
                # WHERE date_to_send = HEUTE AND sent_status = 0
                post = self.db.get_due_daily_post() 
                
                if post:
                    post_id, text, img_path = post
                    logger.info("Daily Service: Neue Nachricht für heute gefunden (ID: %s).", post_id)
                    self._broadcast(text, img_path)
                    self.db.mark_post_as_sent(post_id)
                    logger.info("Daily Service: Nachricht %s als gesendet markiert.", post_id)
                else:
                    # Kein Post in DB → Fallback: 1× pro Tag „Hallo! Drück /start“ in User-Sprache
                    global _last_fallback_date
                    if _last_fallback_date != today:
                        self._broadcast_fallback()
                        _last_fallback_date = today

                # generation_errors: Einträge älter als 7 Tage löschen (1× pro Tag)
                global _last_errors_cleanup_date
                if _last_errors_cleanup_date != today:
                    self.db.cleanup_old_generation_errors()
                    _last_errors_cleanup_date = today

                # Azamat 2× täglich: generierte Begrüßung an bekannte User
                self._maybe_send_azamat_greetings()

                # RSS-Watcher: Bei neuen Meldungen an alle senden (mind. Cooldown dazwischen).
                self._maybe_broadcast_new_rss_news()

            except Exception as e:
                logger.warning("Fehler im Daily Service Loop: %s", e)

            # Prüfe alle 60 Sekunden
            time.sleep(60) 

    def _broadcast(self, text, img_path):
        """Sendet den Inhalt an alle User, die Daily News aktiviert haben."""
        
        # WICHTIG: Überspringen, wenn weder Text noch Bild vorhanden sind.
        if (not text or not text.strip()) and (not img_path or not img_path.strip()):
            logger.info("Daily Service: Weder Text noch Bild vorhanden. Broadcast übersprungen.")
            return

        try:
            users = self.db.get_subscribed_users() # Holt IDs mit daily_msg = 1
            
            if not users:
                logger.info("Daily Service: Keine Abonnenten gefunden.")
                return

            logger.info("Daily Service: sende an %s Empfänger.", len(users))
            
            success_count = 0
            for user_id in users:
                try:
                    settings = self.db.get_user_settings(user_id)
                    user_lang = settings.get("lang", "en") or "en"
                    out_text = _resolve_daily_message_text(text, user_lang)
                    sent = False

                    # Fall A: Nachricht mit Bild
                    if img_path and img_path.strip():
                        # Prüfen ob URL (http) oder lokaler Pfad
                        if img_path.startswith("http"):
                            self.bot.send_photo(
                                user_id, img_path, caption=out_text or None, parse_mode="HTML"
                            )
                            sent = True
                        else:
                            # Prüfen ob lokale Datei existiert
                            try:
                                with open(img_path, "rb") as f:
                                    self.bot.send_photo(
                                        user_id, f, caption=out_text or None, parse_mode="HTML"
                                    )
                                sent = True
                            except FileNotFoundError:
                                # Fallback: Nur Text senden, wenn Bild fehlt und Text vorhanden ist
                                if out_text:
                                    self.bot.send_message(user_id, out_text, parse_mode="HTML")
                                    sent = True

                    # Fall B: Nur Text, aber nur wenn Text auch Inhalt hat
                    elif out_text:
                        self.bot.send_message(user_id, out_text, parse_mode="HTML")
                        sent = True

                    if sent:
                        # Daily-Ausspielungen in globale Chat-Session des Users schreiben.
                        if out_text:
                            append_global_chat_event(self.db, user_id, "assistant", out_text)
                        elif img_path and img_path.strip():
                            append_global_chat_event(self.db, user_id, "assistant", "[daily_image]")
                        success_count += 1

                    # Kurze Pause, um Telegram Limits (Rate Limits) nicht zu verletzen
                    time.sleep(0.05) 
                    
                except Exception:
                    # Optional: User deaktivieren bei "Bot was blocked by the user"
                    pass

            logger.info("Broadcast beendet. Erfolgreich: %s/%s", success_count, len(users))
        except Exception as e:
            logger.warning("Kritischer Fehler im Broadcast: %s", e)

    def _broadcast_fallback(self):
        """Sendet Fallback-Nachricht (Hallo, /start) in der Sprache jedes Users, wenn keine DB-Nachricht da ist."""
        try:
            users = self.db.get_subscribed_users()
            if not users:
                return
            logger.info("Daily Fallback: sende an %s User (kein DB-Post für heute).", len(users))
            success = 0
            for user_id in users:
                try:
                    settings = self.db.get_user_settings(user_id)
                    lang = settings.get("lang", "en")
                    user_name = self.db.get_user_username_or_name(user_id) or ""
                    text = get_random_daily_fallback(lang, user_name)
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(get_text("kb_main", lang), callback_data="nav_main"))
                    self.bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
                    append_global_chat_event(self.db, user_id, "assistant", text)
                    success += 1
                    time.sleep(0.05)
                except Exception:
                    pass
            logger.info("Daily Fallback: %s/%s erfolgreich.", success, len(users))
        except Exception as e:
            logger.warning("Fehler beim Daily Fallback: %s", e)

    def _maybe_send_azamat_greetings(self):
        """Sendet 2× täglich eine von Azamat generierte Begrüßung an User mit daily_msg=1."""
        if not self.generation_service:
            return
        hours_str = os.getenv("AZAMAT_GREETING_HOURS", "8,18")
        try:
            greeting_hours = [int(h.strip()) for h in hours_str.split(",") if h.strip()]
        except (ValueError, TypeError):
            greeting_hours = [8, 18]
        if not greeting_hours:
            return

        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        current_hour = now.hour

        # Prüfen ob wir in einem Greeting-Slot sind (ganze Stunde)
        slot = None
        for i, h in enumerate(greeting_hours):
            if current_hour == h:
                slot = i
                break
        if slot is None:
            return

        global _last_azamat_slots_done
        key = (today, slot)
        if key in _last_azamat_slots_done:
            return
        _last_azamat_slots_done.add(key)
        _last_azamat_slots_done = {k for k in _last_azamat_slots_done if k[0] == today}

        model = self.db.get_model_by_key(AZAMAT_GREETING_MODEL)
        if not model or "text" not in (model.type or []):
            logger.info("Azamat Greeting: Text-Modell nicht verfügbar.")
            return

        users = self.db.get_subscribed_users()
        if not users:
            return

        logger.info("Azamat Greeting Slot %s (%s): sende an %s User.", slot, today, len(users))
        success = 0
        for user_id in users:
            try:
                if self.db.has_azamat_greeting_been_sent(user_id, today, slot):
                    continue
                settings = self.db.get_user_settings(user_id)
                lang = settings.get("lang", "en")
                user_name = self.db.get_user_username_or_name(user_id)
                prompt_tpl = get_text("azamat_daily_greeting_prompt", lang)
                prompt = f"{prompt_tpl}\n\nPerson's name: {user_name or 'User'}\n\nOutput ONLY the greeting text, nothing else."

                ok, result = self.generation_service.process_request(
                    user_id, model, prompt, media_files=None, no_charge=True
                )
                if not ok or not result:
                    continue
                self.bot.send_message(user_id, str(result), parse_mode="HTML")
                append_global_chat_event(self.db, user_id, "assistant", str(result))
                self.db.mark_azamat_greeting_sent(user_id, today, slot)
                success += 1
                time.sleep(0.08)
            except Exception:
                pass
        if success:
            logger.info("Azamat Greeting: %s/%s gesendet.", success, len(users))

    def _fetch_ai_news_from_rss(self, max_items: int = 2) -> list:
        """
        Lädt aktuelle AI-News aus mehreren RSS-Feeds und dedupliziert Einträge.
        Rückgabe: Liste von {title, snippet, link, source, published_ts}
        """
        try:
            combined = []
            for url in AI_NEWS_RSS_URLS:
                feed = feedparser.parse(url)
                feed_title = getattr(feed.feed, "title", "") or url
                entries = getattr(feed, "entries", [])[: max(2, max_items * 3)]
                for entry in entries:
                    title = (getattr(entry, "title", "") or "").strip()
                    # description kann HTML enthalten
                    desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
                    desc = re.sub(r"<[^>]+>", "", desc).strip()
                    link = (getattr(entry, "link", "") or "").strip()
                    published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                    published_ts = int(time.mktime(published)) if published else 0
                    if title:
                        combined.append(
                            {
                                "title": title,
                                "snippet": desc[:300],
                                "link": link,
                                "source": feed_title,
                                "published_ts": published_ts,
                            }
                        )

            # Dedupe per Link (fallback: Titel)
            seen = set()
            deduped = []
            for item in sorted(combined, key=lambda x: x.get("published_ts", 0), reverse=True):
                k = item.get("link") or item.get("title")
                if not k or k in seen:
                    continue
                seen.add(k)
                deduped.append(item)
                if len(deduped) >= max_items:
                    break
            return deduped
        except Exception as e:
            logger.warning("RSS-Fetch fehlgeschlagen: %s", e)
            return []

    def _resolve_news_image_model(self):
        """
        Sucht ein Bildmodell für Daily-News.
        Priorität:
        1) AZAMAT_NEWS_IMAGE_MODEL_KEY
        2) bekannte Keys
        3) Modellname/replicate_id mit 'nano-banana'
        """
        candidates = []
        env_key = (os.getenv("AZAMAT_NEWS_IMAGE_MODEL_KEY") or "").strip()
        if env_key:
            candidates.append(env_key)
        candidates.extend(["nano-banana-pro", "nano-banana", "google-nano-banana-pro", "google-nano-banana"])
        for key in candidates:
            model = self.db.get_model_by_key(key)
            if model and model.is_active and "image" in (model.type or []):
                return model
        for model in self.db.get_all_models():
            rep_id = (model.replicate_id or "").lower()
            name = (model.name or "").lower()
            if not model.is_active:
                continue
            if "image" not in (model.type or []):
                continue
            if "nano-banana" in rep_id or "nano banana" in name:
                return model
        return None

    @staticmethod
    def _extract_first_media_url(result_data):
        if not result_data:
            return None
        if isinstance(result_data, str):
            return result_data.strip() or None
        if isinstance(result_data, (list, tuple)):
            for it in result_data:
                if isinstance(it, str) and it.strip():
                    return it.strip()
            return None
        # Bei Generator/Iterator aus manchen Clients
        try:
            for it in result_data:
                if isinstance(it, str) and it.strip():
                    return it.strip()
        except Exception:
            pass
        return None

    def _maybe_send_ai_news_post(self):
        """5×/Tag: Holt AI-News aus RSS, fasst/übersetzt mit Gemini und postet inkl. Nano-Banana-Bild."""
        return self._dispatch_ai_news_post(force=False)

    def trigger_ai_news_post(self) -> dict:
        """
        Manueller Admin-Trigger für AI-News.
        Erzwingt einen Lauf unabhängig von Zufallsrate/Tageslimit und sendet an ALLE Empfänger.
        """
        return self._dispatch_ai_news_post(force=True, broadcast_all=True)

    @staticmethod
    def _build_news_signature(news_items: list[dict]) -> str:
        """Stabile Signatur aus den Top-News (Link/Titel), um neue Meldungen zu erkennen."""
        parts = []
        for n in news_items[:3]:
            link = (n.get("link") or "").strip()
            title = (n.get("title") or "").strip()
            parts.append(link or title)
        return "|".join(parts).strip()

    def _maybe_broadcast_new_rss_news(self) -> None:
        """
        Beobachtet RSS und sendet bei neuen Meldungen an ALLE Empfänger.
        Sicherheitsnetz:
        - nur wenn Signatur neu ist
        - mindestens RSS_WATCH_MIN_INTERVAL_SECONDS zwischen Aussendungen
        """
        news_items = self._fetch_ai_news_from_rss(max_items=2)
        if len(news_items) < 2:
            return
        signature = self._build_news_signature(news_items)
        if not signature:
            return

        last_sig = self.db.get_bot_setting("rss_last_sent_signature", "")
        if signature == last_sig:
            return

        now_ts = int(time.time())
        last_ts_raw = self.db.get_bot_setting("rss_last_sent_ts", "0")
        try:
            last_ts = int((last_ts_raw or "0").strip())
        except (ValueError, TypeError):
            last_ts = 0

        if last_ts > 0 and (now_ts - last_ts) < RSS_WATCH_MIN_INTERVAL_SECONDS:
            return

        result = self._dispatch_ai_news_post(
            force=True,
            broadcast_all=True,
            preloaded_news_items=news_items,
        )
        if result.get("ok"):
            self.db.set_bot_setting("rss_last_sent_signature", signature)
            self.db.set_bot_setting("rss_last_sent_ts", str(now_ts))

    def _dispatch_ai_news_post(
        self,
        force: bool = False,
        broadcast_all: bool = False,
        preloaded_news_items: list[dict] | None = None,
    ) -> dict:
        """
        Gemeinsame Dispatch-Logik für Scheduler und manuellen Trigger.
        Rückgabe:
        {
          ok: bool,
          reason: str,
          sent_to: int|None,
          target_type: str|None,
          sent_count: int,
          total_recipients: int,
        }
        """
        if not self.generation_service:
            return {"ok": False, "reason": "generation_service_missing", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}
        max_per_day = int(os.getenv("AZAMAT_RANDOM_POSTS_PER_DAY", "5"))
        if max_per_day <= 0 and not force:
            return {"ok": False, "reason": "disabled_by_limit", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}
        sent_today = self.db.get_azamat_random_count_today()
        if sent_today >= max_per_day and not force:
            return {"ok": False, "reason": "daily_limit_reached", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}
        if not force and random.random() > 0.10:
            return {"ok": False, "reason": "random_skip", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}
        model = self.db.get_model_by_key(AZAMAT_GREETING_MODEL)
        if not model or "text" not in (model.type or []):
            return {"ok": False, "reason": "text_model_missing", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}

        news_items = preloaded_news_items if preloaded_news_items is not None else self._fetch_ai_news_from_rss(max_items=2)
        if len(news_items) < 2:
            return {"ok": False, "reason": "not_enough_news_items", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}

        news_block = "\n\n".join(
            f"News {i+1}:\nSource: {n.get('source','')}\nTitle: {n['title']}\nSnippet: {n['snippet']}\nLink: {n.get('link', '')}"
            for i, n in enumerate(news_items)
        )

        recipients = []
        for chat_id in self.db.get_all_tracked_groups():
            lang = self.db.get_group_language(chat_id)
            recipients.append(("group", chat_id, lang))
        for user_id in self.db.get_subscribed_users():
            settings = self.db.get_user_settings(user_id)
            lang = settings.get("lang", "en")
            recipients.append(("user", user_id, lang))
        if not recipients:
            return {"ok": False, "reason": "no_recipients", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}

        targets = recipients if broadcast_all else [random.choice(recipients)]
        sent_count = 0
        first_sent_to = None
        first_type = None
        image_model = self._resolve_news_image_model()
        for target_type, target_id, lang in targets:
            prompt_tpl = get_text("azamat_news_summary_prompt", lang)
            prompt = f"{prompt_tpl}\n\n---\n{news_block}\n---\n\nOutput ONLY the summarized news text."
            user_id_for_gen = target_id if target_type == "user" else (self.db.get_subscribed_users() or [target_id])[0]
            ok, result = self.generation_service.process_request(
                user_id_for_gen, model, prompt, media_files=None, no_charge=True
            )
            if not ok or not result or not str(result).strip():
                continue
            text = str(result).strip()
            self.bot.send_message(target_id, text, parse_mode="HTML")
            if target_type == "user":
                append_global_chat_event(self.db, target_id, "assistant", text)

            # Optionales Daily-News-Bild via Nano Banana
            if image_model:
                image_prompt = (
                    "Create a visually striking editorial AI-news image, futuristic and clean, "
                    "no text, no logos, no watermarks. Themes:\n\n"
                    f"{news_block}\n\n"
                    "Style: modern digital illustration, cinematic lighting, high detail."
                )
                ok_img, img_result = self.generation_service.process_request(
                    user_id_for_gen,
                    image_model,
                    image_prompt,
                    media_files=None,
                    no_charge=True,
                )
                if ok_img:
                    image_url = self._extract_first_media_url(img_result)
                    if image_url:
                        self.bot.send_photo(target_id, image_url)
                        if target_type == "user":
                            append_global_chat_event(self.db, target_id, "assistant", "[daily_news_image]")
            if first_sent_to is None:
                first_sent_to = target_id
                first_type = target_type
            sent_count += 1
            time.sleep(0.05)

        if sent_count <= 0:
            return {"ok": False, "reason": "summary_generation_failed", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": len(targets)}

        if not force:
            self.db.increment_azamat_random_count_today()
        logger.info("Azamat AI News dispatch done: sent=%s/%s (force=%s, broadcast_all=%s).", sent_count, len(targets), force, broadcast_all)
        return {
            "ok": True,
            "reason": "sent",
            "sent_to": first_sent_to,
            "target_type": first_type,
            "sent_count": sent_count,
            "total_recipients": len(targets),
        }