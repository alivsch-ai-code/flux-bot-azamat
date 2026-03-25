"""
Projekt-Einstieg (Production Entrypoint).

Dieser Serverprozess kombiniert zwei Aufgaben:

1) Telegram-Bot (Polling)
   - `telebot.TeleBot.infinity_polling(...)` empfängt Updates
   - `setup_bot(...)` registriert alle Telegram Handler

2) Flask Webserver (Mini-App + JSON APIs)
   - `register_flask_routes(...)` registriert:
     - `GET /webapp` (liefert den React-Vite Build aus `webapp-react/dist`)
     - `GET /webapp/<assets>` (Vite Assets)
     - `POST /api/*` (WebApp Aktionen, User Infos, Strings, Model-Daten, Uploads)

Warum das so ist:
- Telegram-Updates laufen asynchron zum Webserver.
- Die WebApp/Flask-Endpunkte brauchen Zugriff auf:
  - `DatabaseManager` (Neon-PostgreSQL)
  - den Bot (für Aktionen/Antwortflow)
- Deshalb hängt `main` die Referenzen in ein gemeinsames Runtime-Objekt
  (`AppRuntime`) und übergibt es an `src.presentation.http.http_routes`.
"""
import logging
import os
import sys
import threading
import time

import telebot
from flask import Flask

from src.application.services import GenerationService
from src.config.settings import config
from src.infrastructure.ai.unified_client import UnifiedAIClient
from src.infrastructure.database import DatabaseManager
from src.infrastructure.metrics import get_stats
from src.presentation.http.http_routes import AppRuntime, register_flask_routes
from src.presentation.telegram.bot import setup_bot
from src.utils.temp_cleanup import cleanup_temp_folder

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app_runtime = AppRuntime()
# HTTP-Endpunkte registrieren (Mini-App + JSON APIs).
register_flask_routes(app, app_runtime, project_root=_PROJECT_ROOT)


def run_web_server():
    logger.info("Starte Webserver auf Port %s (Waitress, multi-thread)...", config.PORT)
    from waitress import serve

    serve(app, host="0.0.0.0", port=config.PORT, threads=8)


def get_status_text() -> str:
    """Kompakte Statuszeile für RAM/CPU (Log-Bot)."""
    try:
        import psutil
    except ImportError:
        return "🖥 Systemstatus: psutil nicht installiert – kein Ressourcen-Monitoring verfügbar."

    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / 1024 / 1024
    cpu_usage = psutil.cpu_percent(interval=1)

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
            lines.append(f"- {name}: avg {avg_ms:.1f} ms (last {last_ms:.1f} ms, n={int(data.get('count', 0))})")

    return "\n".join(lines)


def start_log_status_loop() -> None:
    log_bot_token = os.getenv("LOG_BOT_ALOSCHA")
    if not log_bot_token:
        logger.info("LOG_BOT_ALOSCHA nicht gesetzt – Status-Log deaktiviert.")
        return

    admin_id_raw = os.getenv("LOG_ADMIN_ID") or os.getenv("ADMIN_ID")
    if not admin_id_raw:
        logger.warning("LOG_ADMIN_ID/ADMIN_ID nicht gesetzt – Status-Log deaktiviert.")
        return

    interval = int(os.getenv("LOG_INTERVAL_SECONDS", "120"))
    admin_id = int(admin_id_raw)
    log_bot = telebot.TeleBot(log_bot_token)

    def _loop():
        time.sleep(10)
        while True:
            try:
                cleanup_temp_folder(max_age_seconds=3600)
                text = get_status_text()
                log_bot.send_message(admin_id, text, parse_mode="HTML")
            except Exception as e:
                logger.warning("Konnte Status-Log nicht senden: %s", e)
            time.sleep(interval)

    threading.Thread(target=_loop, daemon=True).start()


def main():
    # 1) Logging konfigurieren (wichtig für Railway/Render Log-Filtering)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("TeleBot").setLevel(logging.WARNING)
    logger.info("Initialisiere Bot System...")

    # 2) Persistenter Zustand: DB Verbindung (Neon/PostgreSQL)
    db = DatabaseManager()
    logger.info("Datenbank verbunden (PostgreSQL via Neon).")

    # 3) Unified Inference Entry: ein Client, der alle Provider/Modelle verdrahtet.
    ai_provider = UnifiedAIClient(config)
    # 4) Business Layer: Credits/Validation/Routering + Pipeline-Sonderfälle.
    generation_service = GenerationService(repo=db, ai=ai_provider)
    logger.info("Service Layer initialisiert.")

    try:
        bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    except Exception as e:
        logger.critical("Fehler beim Erstellen des Bots: %s", e)
        sys.exit(1)

    # 5) Telegram Handler verdrahten (Orchestrierung + Sub-Handler registrieren)
    setup_bot(bot, generation_service, db)
    logger.info("Telegram Handler registriert.")

    # 6) Flask Endpunkte brauchen DB/Bot, um `/api/webapp_action` auszuführen.
    app_runtime.db = db
    app_runtime.bot = bot
    threading.Thread(target=run_web_server, daemon=True).start()

    start_log_status_loop()

    logger.info("Bot ist bereit (Umgebung: %s)", config.APP_ENV)

    # 7) Webhook entfernen (falls aktiv), sonst kann es zu 409 Conflicts kommen.
    try:
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook entfernt (falls vorhanden).")
    except Exception as e:
        logger.warning("delete_webhook fehlgeschlagen (nicht kritisch): %s", e)

    poll_delay = int(os.getenv("TELEGRAM_POLL_START_DELAY", "25"))
    if poll_delay > 0:
        logger.info("Warte %ds vor erstem Polling (alte Instanz freigeben)...", poll_delay)
        time.sleep(poll_delay)

    retry_delay_409 = int(os.getenv("TELEGRAM_409_RETRY_DELAY", "30"))
    # 8) Polling Loop mit Retry-Logik:
    #    - Timeout -> kurze Pause und neu starten
    #    - 409 Conflict -> warten, weil evtl. noch eine alte Instanz pollt
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                logger.warning("Telegram Polling Timeout – starte in 5s neu: %s", e)
                time.sleep(5)
            elif "409" in err_str or "conflict" in err_str or "getupdates" in err_str:
                logger.warning(
                    "Telegram 409 Conflict (anderer Poller aktiv) – warte %ds, retry: %s",
                    retry_delay_409,
                    e,
                )
                time.sleep(retry_delay_409)
            else:
                logger.critical("Kritischer Absturz: %s", e)
                sys.exit(1)


if __name__ == "__main__":
    main()
