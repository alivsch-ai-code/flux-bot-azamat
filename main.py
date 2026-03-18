import logging
import sys
import threading
import time
import telebot
from flask import Flask

# --- 1. KONFIGURATION (lädt .env via settings) ---
from src.config.settings import config

logger = logging.getLogger(__name__)

# --- 2. INFRASTRUKTUR (WERKZEUGE) ---
from src.infrastructure.ai.unified_client import UnifiedAIClient
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
    logger.info("Starte Webserver auf Port %s...", config.PORT)
    app.run(host='0.0.0.0', port=config.PORT, use_reloader=False)

# --- HAUPTPROGRAMM ---
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Initialisiere Bot System...")

    # SCHRITT A: Datenbank verbinden
    db = DatabaseManager()
    logger.info("Datenbank verbunden (PostgreSQL via Neon).")

    # SCHRITT B: Service Layer erstellen
    ai_provider = UnifiedAIClient(config)
    generation_service = GenerationService(repo=db, ai=ai_provider)
    logger.info("Service Layer initialisiert.")

    # SCHRITT C: Telegram Bot vorbereiten
    try:
        bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    except Exception as e:
        logger.critical("Fehler beim Erstellen des Bots: %s", e)
        sys.exit(1)

    # SCHRITT D: Bot mit Logik verkabeln (Modelle aus db)
    setup_bot(bot, generation_service, db)
    logger.info("Telegram Handler registriert.")

    # SCHRITT E: Webserver starten
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    # SCHRITT F: Bot starten (mit Retry bei Timeout/Netzwerk)
    logger.info("Bot ist bereit (Umgebung: %s)", config.APP_ENV)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                logger.warning("Telegram Polling Timeout – starte in 5s neu: %s", e)
                time.sleep(5)
            else:
                logger.critical("Kritischer Absturz: %s", e)
                sys.exit(1)


if __name__ == "__main__":
    main()