import threading
import time
import telebot
import os
from flask import Flask
# WICHTIG: Für lokale .env Dateien
from dotenv import load_dotenv 

# 1. GANZ OBEN: Umgebungsvariablen laden (.env Datei lesen)
# Das muss passieren, BEVOR irgendetwas anderes passiert!
load_dotenv()

# --- 1. KONFIGURATION & MODELLE ---
from src.config.settings import config
# HINWEIS: Stelle sicher, dass AI_MODELS hier die aktualisierte Liste (mit Credits) ist.
from src.domain.models import AI_MODELS 

# --- 2. INFRASTRUKTUR (WERKZEUGE) ---
from src.infrastructure.ai.unified_client import UnifiedAIClient
# NEU: Datenbank Manager importieren
from src.infrastructure.database import DatabaseManager 

# --- 3. APPLICATION (LOGIK) ---
from src.application.services import GenerationService

# --- 4. PRESENTATION (UI) ---
from src.presentation.telegram.bot import setup_bot

# --- WEBSERVER SETUP ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "🤖 System Status: ONLINE", 200

def run_web_server():
    print(f"🌍 Starte Webserver auf Port {config.PORT}...")
    app.run(host='0.0.0.0', port=config.PORT, use_reloader=False)

# --- HAUPTPROGRAMM ---
def main():
    print("🚀 Initialisiere Bot System...")

    # SCHRITT A: Datenbank verbinden
    # WICHTIG: Variable muss 'db' heißen (nicht 'b')
    # Die Klasse sucht automatisch nach 'DATABASE_URL' in den Umgebungsvariablen.
    db = DatabaseManager() 
    print("📂 Datenbank verbunden (PostgreSQL via Neon/Render).")

    ai_provider = UnifiedAIClient(config)
    # SCHRITT B: Service Layer erstellen
    generation_service = GenerationService(
        repo=db, 
        ai=ai_provider
    )
    print("✅ Service Layer initialisiert.")

    # SCHRITT C: Telegram Bot vorbereiten
    try:
        bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Bots: {e}")
        return

    # SCHRITT D: Bot mit Logik verkabeln
    # Wir übergeben jetzt die 'db' Instanz
    setup_bot(bot, generation_service, AI_MODELS, db)
    print("✅ Telegram Handler registriert.")

    # SCHRITT E: Webserver starten
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    # SCHRITT F: Bot starten
    print(f"🤖 Bot ist bereit und hört zu! (Umgebung: {config.APP_ENV})")
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ KRITISCHER ABSTURZ: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()