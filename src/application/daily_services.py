import os
import random
import time
import threading
from datetime import datetime

from src.utils.strings import get_random_daily_fallback, get_text

# Fallback nur 1× pro Tag senden, wenn keine DB-Nachricht
_last_fallback_date = None
_last_errors_cleanup_date = None
# Azamat-Begrüßung: bereits gesendete Slots (date, slot)
_last_azamat_slots_done = set()

AZAMAT_GREETING_MODEL = "google-gemini-2-5-flash"


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
        print("✅ Daily Service gestartet.")

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
                    print(f"📢 Daily Service: Neue Nachricht für heute gefunden (ID: {post_id}). Sende...")
                    self._broadcast(text, img_path)
                    self.db.mark_post_as_sent(post_id)
                    print(f"✅ Daily Service: Nachricht {post_id} als gesendet markiert.")
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

                # Azamat Random-Posts: Witz oder Info an Gruppen + User (bis zu N/Tag)
                self._maybe_send_random_azamat_post()

            except Exception as e:
                print(f"⚠️ Fehler im Daily Service Loop: {e}")

            # Prüfe alle 60 Sekunden
            time.sleep(60) 

    def _broadcast(self, text, img_path):
        """Sendet den Inhalt an alle User, die Daily News aktiviert haben."""
        
        # WICHTIG: Überspringen, wenn weder Text noch Bild vorhanden sind.
        if (not text or not text.strip()) and (not img_path or not img_path.strip()):
            print("ℹ️ Daily Service: Weder Text noch Bild zum Senden vorhanden. Broadcast übersprungen.")
            return

        try:
            users = self.db.get_subscribed_users() # Holt IDs mit daily_msg = 1
            
            if not users:
                print("ℹ️ Daily Service: Keine Abonnenten gefunden.")
                return

            print(f"📨 Sende an {len(users)} Empfänger...")
            
            success_count = 0
            for user_id in users:
                try:
                    # Fall A: Nachricht mit Bild
                    if img_path and img_path.strip():
                        # Prüfen ob URL (http) oder lokaler Pfad
                        if img_path.startswith("http"):
                            self.bot.send_photo(user_id, img_path, caption=text, parse_mode="HTML")
                        else:
                            # Prüfen ob lokale Datei existiert
                            try:
                                with open(img_path, "rb") as f:
                                    self.bot.send_photo(user_id, f, caption=text, parse_mode="HTML")
                            except FileNotFoundError:
                                # Fallback: Nur Text senden, wenn Bild fehlt und Text vorhanden ist
                                if text and text.strip():
                                    self.bot.send_message(user_id, text, parse_mode="HTML")

                    # Fall B: Nur Text, aber nur wenn Text auch Inhalt hat
                    elif text and text.strip():
                        self.bot.send_message(user_id, text, parse_mode="HTML")
                    
                    success_count += 1
                    
                    # Kurze Pause, um Telegram Limits (Rate Limits) nicht zu verletzen
                    time.sleep(0.05) 
                    
                except Exception as e:
                    # Optional: User deaktivieren bei "Bot was blocked by the user"
                    # print(f"❌ Fehler beim Senden an {user_id}: {e}")
                    pass

            print(f"🏁 Broadcast beendet. Erfolgreich: {success_count}/{len(users)}")
        except Exception as e:
            print(f"⚠️ Kritischer Fehler im Broadcast: {e}")

    def _broadcast_fallback(self):
        """Sendet Fallback-Nachricht (Hallo, /start) in der Sprache jedes Users, wenn keine DB-Nachricht da ist."""
        try:
            users = self.db.get_subscribed_users()
            if not users:
                return
            print(f"📨 Daily Fallback: Sende an {len(users)} User (kein DB-Post für heute)...")
            success = 0
            for user_id in users:
                try:
                    settings = self.db.get_user_settings(user_id)
                    lang = settings.get("lang", "en")
                    text = get_random_daily_fallback(lang)
                    self.bot.send_message(user_id, text, parse_mode="HTML")
                    success += 1
                    time.sleep(0.05)
                except Exception:
                    pass
            print(f"✅ Daily Fallback: {success}/{len(users)} erfolgreich.")
        except Exception as e:
            print(f"⚠️ Fehler beim Daily Fallback: {e}")

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
            print("ℹ️ Azamat Greeting: Text-Modell nicht verfügbar.")
            return

        users = self.db.get_subscribed_users()
        if not users:
            return

        print(f"🤖 Azamat Greeting Slot {slot} ({today}): Sende an {len(users)} User...")
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
                self.db.mark_azamat_greeting_sent(user_id, today, slot)
                success += 1
                time.sleep(0.08)
            except Exception as e:
                pass
        if success:
            print(f"✅ Azamat Greeting: {success}/{len(users)} gesendet.")

    def _maybe_send_random_azamat_post(self):
        """Sendet bis zu N× täglich zufällige Gemini-Posts (Witz oder Info) an Gruppen + bekannte User."""
        if not self.generation_service:
            return
        max_per_day = int(os.getenv("AZAMAT_RANDOM_POSTS_PER_DAY", "5"))
        if max_per_day <= 0:
            return
        sent_today = self.db.get_azamat_random_count_today()
        if sent_today >= max_per_day:
            return
        # ~10% Chance pro Lauf (alle 60s), um über den Tag verteilt zu senden
        if random.random() > 0.10:
            return
        model = self.db.get_model_by_key(AZAMAT_GREETING_MODEL)
        if not model or "text" not in (model.type or []):
            return

        recipients = []  # (type, id, lang)
        for chat_id in self.db.get_all_tracked_groups():
            lang = self.db.get_group_language(chat_id)
            recipients.append(("group", chat_id, lang))
        for user_id in self.db.get_subscribed_users():
            settings = self.db.get_user_settings(user_id)
            lang = settings.get("lang", "en")
            recipients.append(("user", user_id, lang))

        if not recipients:
            return

        target_type, target_id, lang = random.choice(recipients)
        content_type = random.choice(["joke", "info"])
        key = "azamat_random_joke_prompt" if content_type == "joke" else "azamat_random_info_prompt"
        prompt_tpl = get_text(key, lang)
        user_name = ""
        if target_type == "user":
            user_name = self.db.get_user_username_or_name(target_id)
        if target_type == "user" and user_name and user_name != "User":
            mention_tpl = get_text("azamat_random_mention_name", lang)
            prompt_tpl = f"{prompt_tpl}\n\n{mention_tpl}: {user_name}"
        prompt = f"{prompt_tpl}\n\nOutput ONLY the generated text, nothing else."

        # process_request braucht user_id (no_charge) – bei Gruppen: beliebiger Abonnent
        user_id_for_gen = target_id if target_type == "user" else None
        if not user_id_for_gen:
            users = self.db.get_subscribed_users()
            if not users:
                return
            user_id_for_gen = users[0]

        ok, result = self.generation_service.process_request(
            user_id_for_gen, model, prompt, media_files=None, no_charge=True
        )
        if not ok or not result or not str(result).strip():
            return
        try:
            self.bot.send_message(target_id, str(result), parse_mode="HTML")
            self.db.increment_azamat_random_count_today()
            label = "group" if target_type == "group" else "user"
            print(f"🤖 Azamat Random ({content_type}) an {label} {target_id} gesendet.")
        except Exception:
            pass