import time
import threading
from datetime import datetime

class DailyService:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
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
                # 1. Prüfen: Gibt es für HEUTE einen Post, der noch NICHT gesendet wurde?
                # Die Datenbank-Methode 'get_due_daily_post' sucht nach:
                # WHERE date_to_send = HEUTE AND sent_status = 0
                post = self.db.get_due_daily_post() 
                
                if post:
                    # Erwartet Tuple: (id, message_text, image_path)
                    post_id, text, img_path = post
                    print(f"📢 Daily Service: Neue Nachricht für heute gefunden (ID: {post_id}). Sende...")
                    
                    # 2. Nachricht an alle User verteilen
                    self._broadcast(text, img_path)
                    
                    # 3. Status in DB aktualisieren (sent_status = 1)
                    self.db.mark_post_as_sent(post_id)
                    print(f"✅ Daily Service: Nachricht {post_id} als gesendet markiert.")
                
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