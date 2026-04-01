import json
import os
import random
import re
import time
import threading
import logging
import html
from urllib.parse import parse_qs, unquote, urlparse
from datetime import datetime

import feedparser
import requests

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.application.ai_news_rss_defaults import AI_NEWS_RSS_DEFAULT_URLS
from src.presentation.telegram.handlers.gen.chat_sessions import append_global_chat_event
from src.utils.strings import get_random_daily_fallback, get_text

logger = logging.getLogger(__name__)

# Rückwärtskompatibel (Importe / Skripte): gleiche Liste wie in ai_news_rss_defaults.py
DEFAULT_AI_NEWS_RSS_URLS = list(AI_NEWS_RSS_DEFAULT_URLS)


def _rss_urls_for_fetch(urls: list[str]) -> list[str]:
    """
    Pro Lauf nur eine Teilmenge abfragen (Shuffle), damit viele Feeds nicht jedes Mal
    sequentiell blockieren. 0 oder negativ = alle URLs.
    Env: AI_NEWS_RSS_MAX_FEEDS_PER_FETCH (Standard: 18).
    """
    if not urls:
        return []
    try:
        cap = int(os.getenv("AI_NEWS_RSS_MAX_FEEDS_PER_FETCH", "18"))
    except (ValueError, TypeError):
        cap = 18
    if cap <= 0 or len(urls) <= cap:
        return list(urls)
    shuffled = list(urls)
    random.shuffle(shuffled)
    return shuffled[:cap]


def _rss_urls_from_env_only() -> list[str] | None:
    """Nur Env-Override; None = kein Env gesetzt."""
    raw = (os.getenv("AI_NEWS_RSS_URLS") or "").strip()
    if raw:
        urls = [u.strip() for u in raw.split(",") if u.strip()]
        if urls:
            return urls
    single = (os.getenv("AI_NEWS_RSS_URL") or "").strip()
    if single:
        return [single]
    return None


def resolve_ai_news_rss_urls(db=None) -> list[str]:
    """
    Reihenfolge: AI_NEWS_RSS_URLS / AI_NEWS_RSS_URL (Env) → Neon-Tabelle ai_news_rss_feeds → Code-Default.
    """
    env_urls = _rss_urls_from_env_only()
    if env_urls is not None:
        return env_urls
    if db is not None and hasattr(db, "get_ai_news_rss_feed_urls"):
        try:
            from_db = db.get_ai_news_rss_feed_urls()
        except Exception:
            from_db = []
        if isinstance(from_db, list) and len(from_db) > 0:
            return list(from_db)
    return list(AI_NEWS_RSS_DEFAULT_URLS)

# Fallback nur 1× pro Tag senden, wenn keine DB-Nachricht.
# Wichtig: Datum in bot_settings persistieren — reiner RAM (früher _last_fallback_date)
# resettet bei jedem Deploy und hat alle User erneut mit Fallback-Nachrichten genervt.
BOT_SETTING_DAILY_FALLBACK_SENT_DATE = "daily_fallback_sent_date"
_last_errors_cleanup_date = None
# Azamat-Begrüßung: bereits gesendete Slots (date, slot)
_last_azamat_slots_done = set()

AZAMAT_GREETING_MODEL = "google-gemini-2-5-flash"
RSS_WATCH_MIN_INTERVAL_SECONDS = max(300, int(os.getenv("RSS_WATCH_MIN_INTERVAL_SECONDS", "18000")))


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
        # Laufzeit-Guard gegen Doppelversand bei kurz aufeinanderfolgenden Loop-Läufen.
        self._last_rss_signature_runtime = ""
        self._last_rss_sent_ts_runtime = 0
        # Ein Dispatch (Bild + Gemini + Broadcast) darf nicht parallel laufen (Daily-Thread + Admin-Trigger).
        self._ai_news_dispatch_lock = threading.Lock()

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
                    # Kein Post in DB → Fallback: 1× pro Tag (nur wenn heute noch nicht gesendet)
                    sent_for = (self.db.get_bot_setting(BOT_SETTING_DAILY_FALLBACK_SENT_DATE, "") or "").strip()
                    if sent_for != today:
                        self._broadcast_fallback()
                        self.db.set_bot_setting(BOT_SETTING_DAILY_FALLBACK_SENT_DATE, today)

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
                            self.bot.send_photo_sync(
                                user_id, img_path, caption=out_text or None, parse_mode="HTML"
                            )
                            sent = True
                        else:
                            # Prüfen ob lokale Datei existiert
                            try:
                                with open(img_path, "rb") as f:
                                    self.bot.send_photo_sync(
                                        user_id, f, caption=out_text or None, parse_mode="HTML"
                                    )
                                sent = True
                            except FileNotFoundError:
                                # Fallback: Nur Text senden, wenn Bild fehlt und Text vorhanden ist
                                if out_text:
                                    self.bot.send_message_sync(user_id, out_text, parse_mode="HTML")
                                    sent = True

                    # Fall B: Nur Text, aber nur wenn Text auch Inhalt hat
                    elif out_text:
                        self.bot.send_message_sync(user_id, out_text, parse_mode="HTML")
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
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text=get_text("kb_main", lang), callback_data="nav_main")]]
                    )
                    self.bot.send_message_sync(user_id, text, parse_mode="HTML", reply_markup=markup)
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
                    user_id, model, prompt, media_files=None, no_charge=True, lang=lang
                )
                if not ok or not result:
                    continue
                self.bot.send_message_sync(user_id, str(result), parse_mode="HTML")
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
            for url in _rss_urls_for_fetch(resolve_ai_news_rss_urls(getattr(self, "db", None))):
                feed = feedparser.parse(url)
                feed_title = getattr(feed.feed, "title", "") or url
                entries = getattr(feed, "entries", [])[: max(2, max_items * 3)]
                for entry in entries:
                    title = (getattr(entry, "title", "") or "").strip()
                    # description kann HTML enthalten
                    desc_html = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
                    desc = re.sub(r"<[^>]+>", "", desc_html).strip()
                    raw_link = (getattr(entry, "link", "") or "").strip()
                    link = self._normalize_news_link(raw_link, desc_html)
                    src_title = ""
                    if (not link or "news.google.com" in (urlparse(link).netloc or "").lower()):
                        src = getattr(entry, "source", None) or {}
                        src_href = ""
                        try:
                            src_title = (src.get("title", "") if isinstance(src, dict) else getattr(src, "title", "")) or ""
                            src_href = (src.get("href", "") if isinstance(src, dict) else getattr(src, "href", "")) or ""
                        except Exception:
                            src_title = ""
                            src_href = ""
                        src_href = src_href.strip()
                        if self._is_http_url(src_href):
                            link = src_href
                    link = self._resolve_final_news_url(link)
                    published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
                    published_ts = int(time.mktime(published)) if published else 0
                    if title:
                        source_label = self._clean_source_label(feed_title, src_title, link)
                        combined.append(
                            {
                                "title": title,
                                "snippet": desc[:300],
                                "link": link,
                                "source": source_label,
                                "published_ts": published_ts,
                            }
                        )

            # Dedupe per Link (fallback: Titel)
            seen = set()
            deduped = []
            for item in sorted(combined, key=lambda x: x.get("published_ts", 0), reverse=True):
                link = (item.get("link") or "").strip()
                host = (urlparse(link).netloc or "").lower() if link else ""
                # Google-RSS-Links können wechseln; für stabile Dedupe lieber Titel+Quelle.
                if "news.google.com" in host or not link:
                    k = f"{(item.get('source') or '').strip()}::{(item.get('title') or '').strip()}".lower()
                else:
                    k = link
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

    @staticmethod
    def _clean_source_label(feed_title: str, source_title: str, link: str) -> str:
        """
        Verhindert generische Labels wie 'Artificial Intelligence - Google News'
        und bevorzugt Publisher-Name bzw. Host.
        """
        st = (source_title or "").strip()
        ft = (feed_title or "").strip()
        if st and "google news" not in st.lower():
            return st
        if ft and "google news" not in ft.lower():
            return ft
        host = (urlparse((link or "").strip()).netloc or "").lower()
        host = host.replace("www.", "")
        return host or "News"

    @staticmethod
    def _resolve_final_news_url(link: str, timeout_s: float = 5.0) -> str:
        """
        Löst Redirect-Links (insb. news.google.com) auf finalen Artikel-Link auf.
        Bei Fehlern bleibt Original-Link erhalten.
        """
        raw = (link or "").strip()
        if not raw or not DailyService._is_http_url(raw):
            return raw
        host = (urlparse(raw).netloc or "").lower()
        if "news.google.com" not in host and "google.com" not in host:
            return raw
        try:
            resp = requests.get(raw, allow_redirects=True, timeout=timeout_s, headers={"User-Agent": "Mozilla/5.0"})
            final_url = (resp.url or "").strip()
            if DailyService._is_http_url(final_url):
                return final_url
        except Exception:
            pass
        return raw

    @staticmethod
    def _normalize_news_link(raw_link: str, desc_html: str = "") -> str:
        """
        Versucht Google-Redirect-Links auf die Original-Quelle umzuschreiben.
        Fallback bleibt der ursprüngliche Link.
        """
        link = (raw_link or "").strip()
        if not link:
            return ""
        try:
            parsed = urlparse(link)
            host = (parsed.netloc or "").lower()
            if "news.google.com" not in host:
                return link

            qs = parse_qs(parsed.query or "", keep_blank_values=False)
            for key in ("url", "u", "q"):
                vals = qs.get(key) or []
                for val in vals:
                    candidate = unquote((val or "").strip())
                    if DailyService._is_http_url(candidate) and "news.google.com" not in urlparse(candidate).netloc.lower():
                        return candidate

            # Fallback 1: href-Links aus HTML-Snippet extrahieren.
            html_blob = html.unescape(desc_html or "")
            for m in re.finditer(r'href=["\']([^"\']+)["\']', html_blob, flags=re.IGNORECASE):
                candidate = unquote((m.group(1) or "").strip())
                if DailyService._is_http_url(candidate):
                    c_host = (urlparse(candidate).netloc or "").lower()
                    if "news.google.com" not in c_host and "google.com" not in c_host:
                        return candidate

            # Fallback 2: erste externe URL aus Textfragment ziehen.
            for m in re.finditer(r"https?://[^\s\"'<>]+", html_blob):
                candidate = unquote((m.group(0) or "").strip())
                candidate = candidate.replace("&amp;", "&")
                if DailyService._is_http_url(candidate):
                    c_host = (urlparse(candidate).netloc or "").lower()
                    if "news.google.com" not in c_host and "google.com" not in c_host:
                        return candidate

        except Exception:
            pass
        return link

    def _resolve_news_image_model(self):
        """
        Sucht ein Bildmodell für Daily-News.
        Priorität:
        1) AZAMAT_NEWS_IMAGE_MODEL_KEY
        2) bekannte Keys
        3) Modellname/replicate_id mit 'nano-banana'
        """
        def _supports_image(model) -> bool:
            # robust gegen unterschiedliche Typwerte wie "image_generation"
            return any("image" in str(t).lower() for t in (model.type or []))

        candidates = []
        env_key = (os.getenv("AZAMAT_NEWS_IMAGE_MODEL_KEY") or "").strip()
        if env_key:
            candidates.append(env_key)
        # User-Wunsch: Standardmäßig das einfache Nano Banana verwenden (nicht Pro).
        candidates.extend(["nano-banana", "google-nano-banana", "nano-banana-pro", "google-nano-banana-pro"])
        for key in candidates:
            model = self.db.get_model_by_key(key)
            # Admin-spezifischer Key/known key: Typ notfalls tolerieren, solange aktiv.
            if model and model.is_active:
                return model
        for model in self.db.get_all_models():
            rep_id = (model.replicate_id or "").lower()
            name = (model.name or "").lower()
            if not model.is_active:
                continue
            if ("nano-banana" in rep_id or "nano banana" in name) and _supports_image(model):
                return model
        return None

    @staticmethod
    def _extract_first_media_url(result_data):
        if not result_data:
            return None
        # Replicate FileOutput/Objekte liefern URL als Attribut.
        if hasattr(result_data, "url"):
            try:
                url = str(getattr(result_data, "url") or "").strip()
                return url or None
            except Exception:
                pass
        if isinstance(result_data, str):
            return result_data.strip() or None
        if isinstance(result_data, (list, tuple)):
            for it in result_data:
                if isinstance(it, str) and it.strip():
                    return it.strip()
                if hasattr(it, "url"):
                    try:
                        url = str(getattr(it, "url") or "").strip()
                        if url:
                            return url
                    except Exception:
                        pass
            return None
        # Bei Generator/Iterator aus manchen Clients
        try:
            for it in result_data:
                if isinstance(it, str) and it.strip():
                    return it.strip()
                if hasattr(it, "url"):
                    try:
                        url = str(getattr(it, "url") or "").strip()
                        if url:
                            return url
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    @staticmethod
    def _is_http_url(value: str | None) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        try:
            p = urlparse(value.strip())
            return p.scheme in ("http", "https") and bool(p.netloc)
        except Exception:
            return False

    @staticmethod
    def _compose_daily_news_photo_caption(summary: str, sources_footer: str, max_len: int = 1024) -> str:
        """
        Telegram erlaubt für Foto-Captions ca. 1024 Zeichen. Zusammenfassung + Quellen:
        Quellen stehen am Ende — bei naivem Abschneiden würden sie fehlen; deshalb zuerst
        die Zusammenfassung kürzen und den Quellenblock möglichst vollständig behalten.
        """
        sep = "\n\n"
        s = (summary or "").strip()
        f = (sources_footer or "").strip()
        cap = max(64, min(int(max_len), 1024))
        if not f:
            if len(s) <= cap:
                return s
            return s[: cap - 1].rstrip() + "…"
        if len(f) > cap:
            return f[: cap - 1].rstrip() + "…"
        need_footer = len(sep) + len(f)
        room = cap - need_footer
        if room < 1:
            return f
        if len(s) <= room:
            return s + sep + f
        cut = room - 1
        if cut < 16:
            return f
        trimmed = s[:cut].rstrip()
        while trimmed and trimmed[-1] in ",.;:—–- ":
            trimmed = trimmed[:-1].rstrip()
        return trimmed + "…" + sep + f

    def _billing_user_id_for_news(self, target_type: str, target_id: int) -> int:
        """Für no_charge-News: User-ID für interne Gen-Calls (Credits werden nicht belastet)."""
        if target_type == "user":
            return int(target_id)
        subs = self.db.get_subscribed_users()
        if subs:
            return int(subs[0])
        raw = (os.getenv("ADMIN_ID") or "0").strip()
        try:
            aid = int(raw)
        except (ValueError, TypeError):
            aid = 0
        if aid:
            return aid
        return int(target_id)

    def _send_news_image_with_retry(
        self,
        target_id: int,
        image_url: str,
        caption: str | None = None,
        retries: int = 3,
        delay_s: float = 2.0,
    ) -> bool:
        """
        Versucht das News-Bild mehrfach zu senden, falls CDN/URL noch nicht sofort verfügbar ist.
        """
        for attempt in range(1, retries + 1):
            try:
                # Kein HTML-ParseMode bei Captions: vermeidet Parse-Fehler durch LLM-Text.
                self.bot.send_photo_sync(target_id, image_url, caption=caption)
                return True
            except Exception as e:
                if attempt >= retries:
                    logger.warning("Daily News image send failed for %s after %s attempts: %s", target_id, retries, e)
                    return False
                time.sleep(delay_s)
        return False

    def _generate_news_image_url_with_retry(self, recipients: list[tuple], news_block: str, image_model, retries: int = 2, delay_s: float = 2.0) -> str | None:
        """
        Generiert das News-Bild und wartet/retried bis eine gültige URL verfügbar ist.
        """
        if not image_model:
            return None
        if not recipients:
            return None
        u_row = next((row for row in recipients if row[0] == "user"), None)
        if u_row:
            gen_user_id = int(u_row[1])
        else:
            first = recipients[0]
            gen_user_id = self._billing_user_id_for_news(str(first[0]), int(first[1]))
        image_prompt = (
            "Create a rich editorial illustration for AI/tech news: a layered scene with a clear focal subject "
            "and supporting background context (e.g. research lab atmosphere, abstract neural motifs, data flows, "
            "silhouettes of hardware or holographic panels) that reflects the two stories below—more concrete "
            "visual storytelling than a generic abstract blob, but still clean and not cluttered. "
            "Absolutely no readable text, no logos, no watermarks, no lettering on screens. "
            "Stories and cues:\n\n"
            f"{news_block}\n\n"
            "Style: modern digital illustration, cinematic lighting, depth, high detail, cohesive color grade."
        )
        for attempt in range(1, retries + 1):
            ok_img, img_result = self.generation_service.process_request(
                gen_user_id,
                image_model,
                image_prompt,
                media_files=None,
                no_charge=True,
                lang="en",
                prefer_sync_replicate=True,
            )
            if ok_img:
                candidate_url = self._extract_first_media_url(img_result)
                if self._is_http_url(candidate_url):
                    return candidate_url
                logger.warning("Daily News image result without valid URL (attempt %s/%s): %r", attempt, retries, candidate_url)
            else:
                logger.warning("Daily News image generation failed (attempt %s/%s): %s", attempt, retries, img_result)
            if attempt < retries:
                time.sleep(delay_s)
        return None

    def _maybe_send_ai_news_post(self):
        """5×/Tag: Holt AI-News aus RSS, fasst/übersetzt mit Gemini und postet inkl. Nano-Banana-Bild."""
        return self._dispatch_ai_news_post(force=False)

    def trigger_ai_news_post(self) -> dict:
        """
        Manueller Admin-Trigger für AI-News.
        Erzwingt einen Lauf unabhängig von Zufallsrate/Tageslimit und sendet an ALLE Empfänger.
        """
        logger.info(
            "Azamat AI News: Auslöser = manueller Admin-Trigger (umgeht RSS-Cooldown/Signatur; wait_if_busy bis Lock frei)."
        )
        return self._dispatch_ai_news_post(force=True, broadcast_all=True, wait_if_busy=True)

    @staticmethod
    def _build_news_signature(news_items: list[dict]) -> str:
        """Stabile Signatur aus den Top-News (Link/Titel), um neue Meldungen zu erkennen."""
        parts = []
        for n in news_items[:3]:
            link = (n.get("link") or "").strip()
            title = (n.get("title") or "").strip()
            source = (n.get("source") or "").strip().lower()
            host = (urlparse(link).netloc or "").lower() if link else ""
            if "news.google.com" in host or not link:
                parts.append(f"{source}:{title.lower()}")
            else:
                parts.append(link)
        return "|".join(parts).strip()

    def _maybe_broadcast_new_rss_news(self) -> None:
        """
        Beobachtet RSS und sendet bei neuen Meldungen an ALLE Empfänger.
        Sicherheitsnetz:
        - nur wenn Signatur neu ist
        - mindestens RSS_WATCH_MIN_INTERVAL_SECONDS zwischen Aussendungen
        """
        now_ts = int(time.time())
        # Hard cooldown im Runtime-Kontext: verhindert Doppelposts im Minutentakt.
        if self._last_rss_sent_ts_runtime > 0 and (now_ts - self._last_rss_sent_ts_runtime) < RSS_WATCH_MIN_INTERVAL_SECONDS:
            return

        # Lokaler Guard: schützt vor doppeltem Versand, falls DB-Setting verzögert/fehlerhaft ist.
        if (
            self._last_rss_signature_runtime
            and (now_ts - self._last_rss_sent_ts_runtime) < RSS_WATCH_MIN_INTERVAL_SECONDS
        ):
            return

        news_items = self._fetch_ai_news_from_rss(max_items=5)
        if len(news_items) < 2:
            return
        signature = self._build_news_signature(news_items)
        if not signature:
            return

        last_sig = self.db.get_bot_setting("rss_last_sent_signature", "")
        if signature == last_sig:
            return

        if (
            self._last_rss_signature_runtime
            and signature == self._last_rss_signature_runtime
            and (now_ts - self._last_rss_sent_ts_runtime) < RSS_WATCH_MIN_INTERVAL_SECONDS
        ):
            return

        last_ts_raw = self.db.get_bot_setting("rss_last_sent_ts", "0")
        try:
            last_ts = int((last_ts_raw or "0").strip())
        except (ValueError, TypeError):
            last_ts = 0

        if last_ts > 0 and (now_ts - last_ts) < RSS_WATCH_MIN_INTERVAL_SECONDS:
            return

        logger.info(
            "Azamat AI News: Auslöser = RSS-Watcher (neue Signatur / Cooldown ok, min_interval=%ss).",
            RSS_WATCH_MIN_INTERVAL_SECONDS,
        )
        result = self._dispatch_ai_news_post(
            force=True,
            broadcast_all=True,
            preloaded_news_items=news_items,
            only_chat_ids=None,
        )
        if result.get("ok"):
            self.db.set_bot_setting("rss_last_sent_signature", signature)
            self.db.set_bot_setting("rss_last_sent_ts", str(now_ts))
            self._last_rss_signature_runtime = signature
            self._last_rss_sent_ts_runtime = now_ts

    def post_daily_news_to_channel(self, chat_id: int) -> dict:
        """Sendet einen Daily-News-Lauf nur an einen Channel (force, kein Random-Skip)."""
        return self._dispatch_ai_news_post(
            force=True,
            broadcast_all=True,
            preloaded_news_items=None,
            wait_if_busy=True,
            only_chat_ids=[int(chat_id)],
        )

    def _dispatch_ai_news_post(
        self,
        force: bool = False,
        broadcast_all: bool = False,
        preloaded_news_items: list[dict] | None = None,
        wait_if_busy: bool = False,
        only_chat_ids: list[int] | None = None,
    ) -> dict:
        """
        Gemeinsame Dispatch-Logik für Scheduler und manuellen Trigger.
        ``wait_if_busy=True`` (Admin): blockierend ohne Timeout auf den Lock — kein Abbruch mit ``concurrent_dispatch``.
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

        lock = self._ai_news_dispatch_lock
        if wait_if_busy:
            # Manueller Admin-Trigger: immer warten bis der Lock frei ist (kein Timeout).
            # Sonst bricht der Versand nach z. B. 900s mit concurrent_dispatch ab — Admin soll zuverlässig rausschicken.
            if lock.locked():
                logger.info("Azamat AI News: Admin-Trigger wartet auf freien Dispatch-Lock (ohne Zeitlimit) …")
            lock.acquire(blocking=True)
            acquired = True
        else:
            acquired = lock.acquire(blocking=False)
        if not acquired:
            logger.info("Azamat AI News: überspringe — anderer Dispatch läuft bereits (wait_if_busy=%s).", wait_if_busy)
            return {
                "ok": False,
                "reason": "concurrent_dispatch",
                "sent_to": None,
                "target_type": None,
                "sent_count": 0,
                "total_recipients": 0,
            }

        try:
            return self._dispatch_ai_news_post_locked(
                force=force,
                broadcast_all=broadcast_all,
                preloaded_news_items=preloaded_news_items,
                only_chat_ids=only_chat_ids,
            )
        finally:
            lock.release()

    def _dispatch_ai_news_post_locked(
        self,
        force: bool = False,
        broadcast_all: bool = False,
        preloaded_news_items: list[dict] | None = None,
        only_chat_ids: list[int] | None = None,
    ) -> dict:
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

        news_items = preloaded_news_items if preloaded_news_items is not None else self._fetch_ai_news_from_rss(max_items=5)
        if len(news_items) < 2:
            return {"ok": False, "reason": "not_enough_news_items", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}

        news_block = "\n\n".join(
            f"News {i+1}:\nSource: {n.get('source','')}\nTitle: {n['title']}\nSnippet: {n['snippet']}\nLink: {n.get('link', '')}"
            for i, n in enumerate(news_items)
        )

        def _build_sources_footer(lang: str) -> str:
            # Kompakte, mehrsprachige Quellenangabe als Plaintext mit direkten URLs.
            labels = {
                "de": "Quellen",
                "ru": "Источники",
                "kk": "Дереккөздер",
            }
            label = labels.get(lang, "Sources")
            lines = [f"{label}:"]
            for n in news_items[:2]:
                link = (n.get("link") or "").strip()
                source_name = (n.get("source") or "News").strip()
                title = (n.get("title") or "").strip()
                display = source_name if source_name else (title or "News")
                if link:
                    lines.append(f"- {display}: {link}")
                elif title:
                    lines.append(f"- {title}")
            return "\n".join(lines)

        recipients = []
        only_ids = [int(x) for x in (only_chat_ids or []) if x is not None]

        if only_ids:
            for cid in only_ids:
                lang = "de"
                row = self.db.get_telegram_channel_row(cid)
                if row and (row.get("language") or "").strip():
                    lg = (row.get("language") or "de").strip()
                    lang = lg if lg in ("de", "en", "ru", "kk") else "de"
                else:
                    lang = self.db.get_group_language(cid)
                recipients.append(("channel", cid, lang))
        else:
            for chat_id in self.db.get_all_tracked_groups():
                try:
                    cid = int(chat_id)
                except Exception:
                    continue
                # Privatchats/User: positive Telegram-ID. Gruppen/Supergruppen/Kanäle: negativ.
                # Positive IDs in group_settings würden sonst beim Dedup vor dem User-Eintrag stehen und
                # die persönliche Daily-News-DM (mit User-Sprache) verdrängen — wirkt wie „nur Gruppe/RU“.
                if cid >= 0:
                    logger.warning(
                        "AI News: group_settings chat_id=%s übersprungen (keine Gruppen-ID); vermeidet Konflikt mit User-DMs.",
                        cid,
                    )
                    continue
                if self.db.should_skip_channel_from_group_daily(cid):
                    continue
                lang = self.db.get_group_language(chat_id)
                recipients.append(("group", cid, lang))
            for user_id in self.db.get_subscribed_users():
                settings = self.db.get_user_settings(user_id)
                lang = settings.get("lang", "en")
                recipients.append(("user", user_id, lang))
            for cid, clang in self.db.iter_telegram_channels_daily_news():
                recipients.append(("channel", int(cid), clang))
        if not recipients:
            return {"ok": False, "reason": "no_recipients", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": 0}

        # Dedupe über chat_id (unabhängig vom Typ), damit dieselbe ID nicht doppelt bedient wird.
        # Reihenfolge der Liste: zuerst Gruppen, dann User — bei echter Kollision gewinnt die Gruppe.
        dedup = []
        seen_chat_ids = set()
        for t_type, t_id, t_lang in recipients:
            try:
                cid = int(t_id)
            except Exception:
                continue
            if cid in seen_chat_ids:
                continue
            seen_chat_ids.add(cid)
            dedup.append((t_type, cid, t_lang))

        # User zuerst: Daily-News per DM in der jeweiligen UI-Sprache vor Gruppen/Channels.
        dedup.sort(key=lambda row: (0 if row[0] == "user" else 1, row[1]))

        targets = dedup if broadcast_all else [random.choice(dedup)]
        if broadcast_all and targets:
            n_u = sum(1 for t, _, _ in targets if t == "user")
            n_g = sum(1 for t, _, _ in targets if t == "group")
            n_c = sum(1 for t, _, _ in targets if t == "channel")
            langs = sorted({((lg or "en").strip() or "en") for _, _, lg in targets})
            logger.info(
                "Azamat AI News: Zielverteilung — %s User-DM(s), %s Gruppe(n), %s Channel(s); Sprachen: %s.",
                n_u,
                n_g,
                n_c,
                langs,
            )
        sent_count = 0
        first_sent_to = None
        first_type = None
        image_model = self._resolve_news_image_model()
        # Summary wird einmal pro Sprache erzeugt und dann wiederverwendet.
        summary_by_lang: dict[str, str] = {}
        # Bild wird einmal pro Batch generiert; Trigger wartet bis URL vorhanden oder Retry-Limit erreicht.
        batch_image_url = self._generate_news_image_url_with_retry(dedup, news_block, image_model, retries=3, delay_s=2.0)
        logger.info(
            "Azamat AI News: Bild-URL %s (%s Empfänger, %s Ziel(e) im Lauf).",
            "ok" if batch_image_url else "fehlt",
            len(dedup),
            len(targets),
        )

        for target_type, target_id, lang in targets:
            lang_key = (lang or "en").strip() or "en"
            if lang_key not in summary_by_lang:
                prompt_tpl = get_text("azamat_news_summary_prompt", lang_key)
                prompt = (
                    f"{prompt_tpl}\n\n---\n{news_block}\n---\n\n"
                    "Also add one subtle, practical future recommendation for readers. "
                    "Stay cheeky and blunt, but keep it useful.\n\n"
                    "Output ONLY the summarized news text."
                )
                user_id_for_gen = self._billing_user_id_for_news(target_type, target_id)
                t0 = time.perf_counter()
                logger.info("Azamat AI News: starte Zusammenfassung für Sprache %s …", lang_key)
                ok, result = self.generation_service.process_request(
                    user_id_for_gen,
                    model,
                    prompt,
                    media_files=None,
                    no_charge=True,
                    lang=lang_key,
                    prefer_sync_replicate=True,
                )
                dt = time.perf_counter() - t0
                if not ok or not result or not str(result).strip():
                    logger.warning(
                        "Azamat AI News: Zusammenfassung %s fehlgeschlagen nach %.1fs (ok=%s, result=%r)",
                        lang_key,
                        dt,
                        ok,
                        (str(result)[:200] + "…") if result and len(str(result)) > 200 else result,
                    )
                    continue
                logger.info("Azamat AI News: Zusammenfassung %s fertig in %.1fs.", lang_key, dt)
                summary_text = str(result).strip()
                summary_by_lang[lang_key] = summary_text

            text = summary_by_lang.get(lang_key, "").strip()
            if not text:
                continue
            footer = _build_sources_footer(lang_key)
            final_text = f"{text}\n\n{footer}"
            try:
                logger.info(
                    "Azamat AI News: sende an %s chat_id=%s (text_len=%s, mit_bild=%s)",
                    target_type,
                    target_id,
                    len(final_text),
                    bool(batch_image_url),
                )
                # Bild + Text getrennt senden: mehr Platz für längeren Text.
                if batch_image_url:
                    sent_img = self._send_news_image_with_retry(
                        target_id,
                        batch_image_url,
                        caption=None,
                        retries=3,
                        delay_s=2.0,
                    )
                    if sent_img:
                        self.bot.send_message_sync(target_id, final_text)
                    else:
                        self.bot.send_message_sync(target_id, final_text)
                else:
                    self.bot.send_message_sync(target_id, final_text)

                if target_type == "user":
                    append_global_chat_event(self.db, target_id, "assistant", final_text)
            except Exception as e:
                # WICHTIG: Einzelne fehlgeschlagene Chats dürfen den Broadcast nicht abbrechen.
                logger.warning("Daily News send failed for %s (%s): %s", target_type, target_id, e)
                continue
            if first_sent_to is None:
                first_sent_to = target_id
                first_type = target_type
            sent_count += 1
            time.sleep(0.05)

        if sent_count <= 0:
            return {"ok": False, "reason": "summary_generation_failed", "sent_to": None, "target_type": None, "sent_count": 0, "total_recipients": len(targets)}

        # Runtime-Marker auch für manuelle Trigger setzen (schützt vor sofortigen Doppelposts).
        self._last_rss_sent_ts_runtime = int(time.time())
        sig_now = self._build_news_signature(news_items)
        if sig_now:
            self._last_rss_signature_runtime = sig_now

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