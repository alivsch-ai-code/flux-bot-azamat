import logging
import os
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


def get_status_text() -> str:
    """Liefert eine kompakte Statuszeile für RAM/CPU."""
    try:
        import psutil  # optional dependency
    except ImportError:
        return "🖥 Systemstatus: psutil nicht installiert – kein Ressourcen-Monitoring verfügbar."

    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / 1024 / 1024
    cpu_usage = psutil.cpu_percent(interval=1)
    return (
        "🖥 <b>Systemstatus (Render)</b>\n\n"
        f"RAM-Verbrauch: <b>{ram_mb:.1f} MB</b>\n"
        f"CPU-Auslastung: <b>{cpu_usage:.1f}%</b>"
    )


def start_log_status_loop(main_bot: telebot.TeleBot) -> None:
    """
    Startet im Hauptprozess einen Hintergrund-Thread, der periodisch
    RAM/CPU an einen Admin schickt. Nutzt den bestehenden Bot/Token.
    """
    admin_id = os.getenv("ADMIN_ID")
    interval = int(os.getenv("LOG_INTERVAL_SECONDS", "3600"))
    if not admin_id:
        logger.warning("ADMIN_ID nicht gesetzt – Status-Log wird deaktiviert.")
        return

    admin_id = int(admin_id)

    def _loop():
        # kleine Startverzögerung, damit der Bot ready ist
        time.sleep(10)
        while True:
            try:
                text = get_status_text()
                main_bot.send_message(admin_id, text, parse_mode="HTML")
            except Exception as e:
                logger.warning("Konnte Status-Log nicht senden: %s", e)
            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()

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

    # SCHRITT F: Status-Log-Loop im Hauptprozess starten
    start_log_status_loop(bot)

    # SCHRITT G: Bot starten (mit Retry bei Timeout/Netzwerk)
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