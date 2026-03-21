import logging
import os
import sys
import threading
import time

import telebot
from flask import Flask, jsonify, request

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
_db_instance = None
_bot_instance = None

@app.route('/')
def health_check():
    return "🤖 System Status: ONLINE", 200

@app.route('/webapp')
def webapp():
    """Telegram Mini App – HTML-Menü"""
    path = os.path.join(os.path.dirname(__file__), "webapp", "index.html")
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}
    except FileNotFoundError:
        return "<h1>Web App nicht gefunden</h1>", 404, {"Content-Type": "text/html; charset=utf-8"}

@app.route('/api/webapp_action', methods=['POST'])
def api_webapp_action():
    """Web App sendet Aktionen per POST (sendData funktioniert nicht bei Menü-Button)."""
    if _db_instance is None:
        return jsonify(ok=False, error="no_db"), 400
    try:
        from src.utils.telegram_init_data import validate_init_data
        from src.presentation.telegram.handlers.menu_handler import process_webapp_action, _is_webapp_mode

        data = request.get_json() or {}
        action = data.get("action", "")
        init_data = data.get("init_data", "")
        if not action or not init_data:
            return jsonify(ok=False, error="missing_params"), 400
        if not _is_webapp_mode(_db_instance):
            return jsonify(ok=False, error="webapp_disabled"), 400

        user_id = validate_init_data(init_data, config.TELEGRAM_TOKEN)
        if not user_id:
            return jsonify(ok=False, error="invalid_init_data"), 403

        if _bot_instance is None:
            return jsonify(ok=False, error="no_bot"), 500

        process_webapp_action(_bot_instance, user_id, action, _db_instance)
        return jsonify(ok=True)
    except Exception as e:
        logger.exception("webapp_action error: %s", e)
        return jsonify(ok=False, error=str(e)), 500


@app.route('/api/user_info', methods=['POST'])
def api_user_info():
    """WebApp: User-Infos (username, credits, lang) via init_data."""
    if _db_instance is None:
        return jsonify(ok=False, error="no_db"), 400
    try:
        from src.utils.telegram_init_data import validate_init_data

        data = request.get_json() or {}
        init_data = data.get("init_data", "")
        if not init_data:
            return jsonify(ok=False, error="missing_init_data"), 400

        user_id = validate_init_data(init_data, config.TELEGRAM_TOKEN)
        if not user_id:
            return jsonify(ok=False, error="invalid_init_data"), 403

        user = _db_instance.get_user(user_id)
        settings = _db_instance.get_user_settings(user_id)
        credits = _db_instance.get_user_credits(user_id)
        return jsonify(ok=True, user_id=user_id, username=user.username or "User", credits=credits, lang=settings["lang"])
    except Exception as e:
        logger.exception("api_user_info error: %s", e)
        return jsonify(ok=False, error=str(e)), 500


@app.route('/api/strings')
def api_strings():
    """WebApp: Lokalisierte Strings für die gewählte Sprache."""
    lang = request.args.get("lang", "de") or "de"
    if lang not in ("de", "en", "ru", "kk"):
        lang = "de"
    try:
        from src.utils.strings import get_webapp_strings
        return jsonify(get_webapp_strings(lang))
    except Exception as e:
        logger.warning("api_strings error: %s", e)
        return jsonify({}), 200


@app.route('/api/models')
def api_models():
    """API für Mini App: Modelle und Unterordner pro menu_path (wie Inline-Menü)."""
    if _db_instance is None:
        return jsonify(models=[], folders=[], title=""), 200
    path = request.args.get("path", "root") or "root"
    try:
        models = _db_instance.get_all_models()
        sub_cats: set[str] = set()
        items = []
        for m in models:
            if m.menu_path == path:
                cost = int(m.custom_price if m.custom_price is not None else m.internal_cost)
                items.append({"key": m.key, "name": m.name, "final_cost": cost})
            elif path == "root" and "/" not in m.menu_path and m.menu_path != "root":
                sub_cats.add(m.menu_path)
            elif path != "root" and m.menu_path.startswith(path + "/"):
                sub_cats.add(m.menu_path[len(path) + 1 :].split("/")[0])
        lang = request.args.get("lang", "de") or "de"
        if lang not in ("de", "en", "ru", "kk"):
            lang = "de"
        try:
            from src.utils.strings import get_text
            titles = {
                "image": get_text("menu_image", lang),
                "video": get_text("menu_video", lang),
                "audio": get_text("menu_audio", lang),
                "text": get_text("menu_text", lang),
                "tools": get_text("menu_tools", lang),
            }
        except Exception:
            titles = {"image": "Bild Studio", "video": "Video Studio", "audio": "Audio Studio", "text": "Text / Chat", "tools": "Werkzeuge"}
        root_title = "Kategorien"
        try:
            from src.utils.strings import get_text
            root_title = get_text("webapp_categories", lang)
        except Exception:
            pass
        title = titles.get(path.split("/")[-1], path.replace("/", " · ").title() if path != "root" else root_title)
        folders = [
            {"path": seg if path == "root" else f"{path}/{seg}", "slug": seg}
            for seg in sorted(sub_cats)
        ]
        return jsonify(models=items, folders=folders, title=title)
    except Exception as e:
        logger.warning("api_models error: %s", e)
        return jsonify(models=[], folders=[], title=""), 200

def run_web_server():
    logger.info("Starte Webserver auf Port %s (Waitress, multi-thread)...", config.PORT)
    from waitress import serve
    serve(app, host='0.0.0.0', port=config.PORT, threads=8)


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

    # SCHRITT E: Webserver starten (db + bot für /api)
    global _db_instance, _bot_instance
    _db_instance = db
    _bot_instance = bot
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
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                logger.warning("Telegram Polling Timeout – starte in 5s neu: %s", e)
                time.sleep(5)
            elif "409" in err_str or "conflict" in err_str:
                logger.warning("Telegram 409 Conflict (andere Instanz?) – warte 30s, dann Retry: %s", e)
                time.sleep(30)
            else:
                logger.critical("Kritischer Absturz: %s", e)
                sys.exit(1)


if __name__ == "__main__":
    main()