"""
Projekt-Einstieg (Production Entrypoint).

1) Telegram-Bot: aiogram 3 + asyncio (`Dispatcher.start_polling`)
2) Flask Webserver (Mini-App + JSON APIs) in einem Hintergrund-Thread (Waitress)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import time
import urllib.error
import urllib.request

from flask import Flask

from src.application.services import GenerationService
from src.config.settings import config
from src.infrastructure.ai.unified_client import UnifiedAIClient
from src.infrastructure.database import DatabaseManager
from src.infrastructure.metrics import get_stats
from src.presentation.http.http_routes import AppRuntime, register_flask_routes
from src.presentation.telegram.bot import create_bot_and_facade, setup_bot
from src.utils.temp_cleanup import cleanup_temp_folder

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app_runtime = AppRuntime()
register_flask_routes(app, app_runtime, project_root=_PROJECT_ROOT)


def run_web_server():
    logger.info("Starte Webserver auf Port %s (Waitress, multi-thread)...", config.PORT)
    from waitress import serve

    serve(app, host="0.0.0.0", port=config.PORT, threads=8)


def get_status_text() -> str:
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


def _telegram_send_message(token: str, chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        resp.read()


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

    def _loop():
        time.sleep(10)
        while True:
            try:
                cleanup_temp_folder(max_age_seconds=3600)
                text = get_status_text()
                _telegram_send_message(log_bot_token, admin_id, text)
            except urllib.error.HTTPError as e:
                logger.warning("Status-Log HTTP-Fehler: %s", e)
            except Exception as e:
                logger.warning("Konnte Status-Log nicht senden: %s", e)
            time.sleep(interval)

    threading.Thread(target=_loop, daemon=True).start()


async def _run_bot_async(db, generation_service) -> None:
    loop = asyncio.get_running_loop()
    bot, facade = create_bot_and_facade(loop)
    app_runtime.db = db
    app_runtime.bot = facade
    app_runtime.generation_service = generation_service

    try:
        me = await bot.get_me()
        app_runtime.bot_username = (getattr(me, "username", None) or "").strip()
        if app_runtime.bot_username:
            logger.info("WebApp: @%s für /api/user_info gecacht (ohne get_me pro Request).", app_runtime.bot_username)
    except Exception as e:
        logger.warning("get_me für WebApp bot_username fehlgeschlagen: %s", e)
        app_runtime.bot_username = ""

    threading.Thread(target=run_web_server, daemon=True).start()
    start_log_status_loop()

    _, dp = await setup_bot(bot, facade, generation_service, db)
    logger.info("Telegram Handler registriert (aiogram).")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook entfernt (falls vorhanden).")
    except Exception as e:
        logger.warning("delete_webhook fehlgeschlagen (nicht kritisch): %s", e)

    poll_delay = int(os.getenv("TELEGRAM_POLL_START_DELAY", "25"))
    if poll_delay > 0:
        logger.info("Warte %ds vor erstem Polling (alte Instanz freigeben)...", poll_delay)
        await asyncio.sleep(poll_delay)

    retry_delay_409 = int(os.getenv("TELEGRAM_409_RETRY_DELAY", "30"))
    logger.info("Bot ist bereit (Umgebung: %s)", config.APP_ENV)

    while True:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                logger.warning("Telegram Polling Timeout – starte in 5s neu: %s", e)
                await asyncio.sleep(5)
            elif "409" in err_str or "conflict" in err_str or "getupdates" in err_str:
                logger.warning(
                    "Telegram 409 Conflict (anderer Poller aktiv) – warte %ds, retry: %s",
                    retry_delay_409,
                    e,
                )
                await asyncio.sleep(retry_delay_409)
            else:
                logger.critical("Kritischer Absturz: %s", e)
                sys.exit(1)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logger.info("Initialisiere Bot System...")

    db = DatabaseManager()
    logger.info("Datenbank verbunden (PostgreSQL via Neon).")

    ai_provider = UnifiedAIClient(config)
    generation_service = GenerationService(db_manager=db, ai_unified_client=ai_provider)
    logger.info("Service Layer initialisiert.")

    try:
        asyncio.run(_run_bot_async(db, generation_service))
    except KeyboardInterrupt:
        logger.info("Beende durch Benutzer.")


if __name__ == "__main__":
    main()
