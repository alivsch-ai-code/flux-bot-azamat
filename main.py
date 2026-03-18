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
from src.infrastructure.metrics import get_stats
from src.utils.temp_cleanup import cleanup_temp_folder

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

    # Metriken auswerten (Durchschnittszeiten in ms)
    stats = get_stats()
    lines = [
        "🖥 <b>Systemstatus (Render)</b>",
        "",
        f"RAM-Verbrauch: <b>{ram_mb:.1f} MB</b>",
        f"CPU-Auslastung: <b>{cpu_usage:.1f}%</b>",
    ]
    if stats:
        lines.append("")
        lines.append("<b>Timings:</b>")
        for name, data in stats.items():
            count = data.get("count", 0) or 1
            avg_ms = (data.get("total", 0.0) / count) * 1000
            last_ms = data.get("last", 0.0) * 1000
            lines.append(f"- {name}: avg {avg_ms:.1f} ms (last {last_ms:.1f} ms, n={int(data.get('count',0))})")

    return "\n".join(lines)


def start_log_status_loop() -> None:
    """
    Startet im Hauptprozess einen Hintergrund-Thread, der periodisch
    RAM/CPU an einen Admin schickt. Nutzt einen separaten Log-Bot-Token.
    """
    log_bot_token = os.getenv("LOG_BOT_ALOSCHA")
    if not log_bot_token:
        logger.info("LOG_BOT_ALOSCHA nicht gesetzt – Status-Log deaktiviert.")
        return

    # Empfänger: eigener Admin, sonst fallback auf ADMIN_ID
    admin_id_raw = os.getenv("LOG_ADMIN_ID") or os.getenv("ADMIN_ID")
    if not admin_id_raw:
        logger.warning("LOG_ADMIN_ID/ADMIN_ID nicht gesetzt – Status-Log deaktiviert.")
        return

    # alle 2 Minuten default
    interval = int(os.getenv("LOG_INTERVAL_SECONDS", "120"))
    admin_id = int(admin_id_raw)
    log_bot = telebot.TeleBot(log_bot_token)

    def _loop():
        # kleine Startverzögerung, damit der Bot ready ist
        time.sleep(10)
        while True:
            try:
                # Temp-Ordner gelegentlich aufräumen (Dateien älter als 1 Stunde)
                cleanup_temp_folder(max_age_seconds=3600)
                text = get_status_text()
                # Wichtig: nur send_message (kein polling) -> kein 409-Konflikt
                log_bot.send_message(admin_id, text, parse_mode="HTML")
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

    # SCHRITT F: Status-Log-Loop im Hauptprozess starten (separater Log-Bot)
    start_log_status_loop()

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