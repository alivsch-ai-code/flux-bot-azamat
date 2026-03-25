import logging
import os
import sys
import threading
import time

import telebot
from flask import Flask, jsonify, redirect, request, send_from_directory

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

def _webapp_react_dist_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "webapp-react", "dist")


@app.route('/webapp')
def webapp():
    """Telegram Mini App – React (Vite build under webapp-react/dist)."""
    dist_dir = _webapp_react_dist_dir()
    index_path = os.path.join(dist_dir, "index.html")
    if not os.path.isfile(index_path):
        return (
            "<h1>Web App Build nicht gefunden</h1><p>Führe <code>npm run build --prefix webapp-react</code> aus.</p>",
            404,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    return send_from_directory(dist_dir, "index.html")


@app.route('/webapp/<path:filename>')
def webapp_assets(filename: str):
    """Static assets from Vite output (e.g. /webapp/assets/…)."""
    dist_dir = _webapp_react_dist_dir()
    try:
        return send_from_directory(dist_dir, filename)
    except Exception:
        return "", 404


@app.route("/webapp-react")
@app.route("/webapp-react/")
def webapp_react_legacy_redirect():
    """Alte BotFather-URLs (base war /webapp-react/); jetzt einheitlich /webapp/."""
    return redirect("/webapp", code=308)


@app.route("/webapp-react/<path:filename>")
def webapp_react_legacy_assets_redirect(filename: str):
    return redirect(f"/webapp/{filename}", code=308)


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

        res_data = process_webapp_action(_bot_instance, user_id, action, _db_instance, payload=data)
        if res_data is None:
            return jsonify(ok=True)
        return jsonify(ok=True, **res_data)
    except ValueError as e:
        logger.info("webapp_action validation error: %s", e)
        return jsonify(ok=False, error=str(e)), 400
    except Exception as e:
        logger.exception("webapp_action error: %s", e)
        return jsonify(ok=False, error="internal_error"), 500


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
        bot_username = ""
        if _bot_instance:
            try:
                me = _bot_instance.get_me()
                bot_username = getattr(me, "username", "") or ""
            except Exception:
                pass
        return jsonify(
            ok=True, user_id=user_id, username=user.username or "User",
            credits=credits, lang=settings["lang"],
            auto_opt=bool(settings.get("auto_opt", True)),
            daily_msg=bool(settings.get("daily_msg", True)),
            bot_username=bot_username,
        )
    except Exception as e:
        logger.exception("api_user_info error: %s", e)
        return jsonify(ok=False, error="internal_error"), 500


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


def _resolve_example_url(example_data: object) -> str:
    """
    Versucht aus `example_data` zuverlässig ein Beispiel-Preview zu finden.
    Für Veo/Kling etc. können sich die Keys/Shapes unterscheiden.
    """
    if not example_data or not isinstance(example_data, dict):
        return ""

    candidates = (
        "output_image",
        "image",
        "url",
        "output_video_thumbnail",
        "output_video",
        "video_thumbnail",
        "thumbnail",
        "preview_image",
    )
    for k in candidates:
        v = example_data.get(k)
        if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
            return v

    # Fallback: rekursiv nach einer http(s)-URL im Beispiel-Objekt suchen.
    def _walk(obj: object) -> str:
        if isinstance(obj, str) and (obj.startswith("http://") or obj.startswith("https://")):
            return obj
        if isinstance(obj, dict):
            for _k, _v in obj.items():
                got = _walk(_v)
                if got:
                    return got
        if isinstance(obj, list):
            for x in obj:
                got = _walk(x)
                if got:
                    return got
        return ""

    return _walk(example_data)


@app.route('/api/model')
def api_model():
    """API für WebApp: Vollständige Modell-Details (Name, Beschreibung, Beispielbild, Kosten)."""
    if _db_instance is None:
        return jsonify(ok=False, error="no_db"), 400
    key = request.args.get("key", "")
    if not key:
        return jsonify(ok=False, error="missing_key"), 400
    try:
        model = _db_instance.get_model_by_key(key)
        if not model or not model.is_active:
            return jsonify(ok=False, error="not_found"), 404
        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
        replicate_id = (model.replicate_id or "")
        is_veo31 = "google/veo-3.1" in replicate_id.lower()
        example_url = ""
        example_prompt = ""
        if model.example_data and isinstance(model.example_data, dict):
            example_url = _resolve_example_url(model.example_data)
            example_prompt = (model.example_data.get("prompt") or model.example_data.get("example_prompt") or "")[:200]
        input_schema = model.input_schema if isinstance(model.input_schema, dict) else {}
        props = input_schema.get("properties") if isinstance(input_schema, dict) else {}
        props = props if isinstance(props, dict) else {}

        def _first_default(*keys, fallback=None):
            for k in keys:
                p = props.get(k)
                if isinstance(p, dict) and "default" in p and p.get("default") is not None:
                    return p.get("default")
            return fallback

        def _enum_or(*keys, fallback=None):
            for k in keys:
                p = props.get(k)
                if isinstance(p, dict) and isinstance(p.get("enum"), list) and p.get("enum"):
                    return p.get("enum")
            return fallback if fallback is not None else []

        generation_options_schema = {
            "duration": {
                "enabled": "duration" in props,
                "default": int(_first_default("duration", fallback=5) or 5),
                "enum": [int(x) for x in _enum_or("duration", fallback=[5, 6, 7, 8]) if str(x).isdigit()],
            },
            "resolution": {
                "enabled": "resolution" in props,
                "default": str(_first_default("resolution", fallback="1080p")),
                "enum": [str(x) for x in _enum_or("resolution", fallback=["720p", "1080p"])],
            },
            "aspect_ratio": {
                "enabled": "aspect_ratio" in props,
                "default": str(_first_default("aspect_ratio", fallback="16:9")),
                "enum": [str(x) for x in _enum_or("aspect_ratio", fallback=["16:9", "9:16", "1:1"])],
            },
            "reference_images": {
                "enabled": "reference_images" in props,
            },
            "generate_audio": {
                "enabled": "generate_audio" in props,
                "default": bool(_first_default("generate_audio", fallback=True)),
            },
        }

        return jsonify(ok=True, key=model.key, name=model.name, description=model.description or "",
            example_image_url=example_url, example_prompt=example_prompt,
            final_cost=final_cost, menu_path=model.menu_path or "root",
            model_type=model.type or [],
            replicate_id=replicate_id,
            input_schema=input_schema,
            generation_options_schema=generation_options_schema,
            veo_options={
                "enabled": is_veo31,
                "default_duration": 5,
                "durations": [5, 6, 7, 8],
                "resolutions": ["720p", "1080p"],
                "aspect_ratios": ["16:9", "9:16", "1:1"],
                "base_cost_for_5s": final_cost,
            })
    except Exception as e:
        logger.warning("api_model error: %s", e)
        return jsonify(ok=False, error="internal_error"), 500


def _replicate_file_url(resp) -> str | None:
    url = getattr(resp, "url", None)
    if not url and hasattr(resp, "urls") and isinstance(resp.urls, dict):
        url = resp.urls.get("get")
    return str(url) if url else None


@app.route("/api/webapp_upload_reference", methods=["POST"])
def api_webapp_upload_reference():
    """
    WebApp: Referenzbilder als Multipart hochladen → Replicate Files API → HTTPS-URLs
    für generation_options.reference_images (wie manuell eingetragene URLs).
    """
    max_bytes = 10 * 1024 * 1024
    max_files = 10
    allowed_mime = frozenset({"image/jpeg", "image/png", "image/webp"})

    if _db_instance is None:
        return jsonify(ok=False, error="no_db"), 400
    try:
        import replicate
        from src.utils.telegram_init_data import validate_init_data
        from src.presentation.telegram.handlers.menu_handler import _is_webapp_mode

        init_data = request.form.get("init_data", "")
        if not init_data:
            return jsonify(ok=False, error="missing_init_data"), 400
        if not _is_webapp_mode(_db_instance):
            return jsonify(ok=False, error="webapp_disabled"), 400

        user_id = validate_init_data(init_data, config.TELEGRAM_TOKEN)
        if not user_id:
            return jsonify(ok=False, error="invalid_init_data"), 403

        files = request.files.getlist("files")
        if not files:
            one = request.files.get("file")
            files = [one] if one and getattr(one, "filename", None) else []
        files = [f for f in files if f and getattr(f, "filename", None)]
        if not files:
            return jsonify(ok=False, error="no_files"), 400
        if len(files) > max_files:
            return jsonify(ok=False, error="too_many_files"), 400

        def _mime_for_upload(fs) -> str:
            ct = (fs.content_type or "").split(";")[0].strip().lower()
            if ct in allowed_mime:
                return ct
            ext = (os.path.splitext(fs.filename or "")[1] or "").lower()
            if ext in (".jpg", ".jpeg"):
                return "image/jpeg"
            if ext == ".png":
                return "image/png"
            if ext == ".webp":
                return "image/webp"
            return ""

        client = replicate.Client(api_token=config.REPLICATE_API_TOKEN)
        urls: list[str] = []
        import io

        for fs in files:
            raw = fs.read()
            if len(raw) > max_bytes:
                return jsonify(ok=False, error="file_too_large"), 400
            mime = _mime_for_upload(fs)
            if mime not in allowed_mime:
                return jsonify(ok=False, error="invalid_type"), 400
            fn = os.path.basename(fs.filename or "image.jpg") or "image.jpg"
            # replicate SDK verlangt hier zwingend `file=` (Pfad oder Datei-Objekt).
            resp = client.files.create(file=io.BytesIO(raw), filename=fn, type=mime)
            url = _replicate_file_url(resp)
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                return jsonify(ok=False, error="upload_failed"), 500
            urls.append(url)

        return jsonify(ok=True, urls=urls)
    except Exception as e:
        logger.exception("webapp_upload_reference error: %s", e)
        return jsonify(ok=False, error="internal_error"), 500


@app.route('/api/shop_packages')
def api_shop_packages():
    """WebApp: Credit-Pakete für den Shop."""
    try:
        from src.presentation.telegram.handlers.payment_handler import CREDIT_PACKAGES
        packages = [
            {"label": lbl, "desc": desc, "price": price, "credits": credits}
            for lbl, desc, price, credits in CREDIT_PACKAGES
        ]
        return jsonify(ok=True, packages=packages)
    except Exception as e:
        logger.warning("api_shop_packages error: %s", e)
        return jsonify(ok=True, packages=[])


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
                example_url = _resolve_example_url(getattr(m, "example_data", None))
                items.append({
                    "key": m.key,
                    "name": m.name,
                    "final_cost": cost,
                    "example_image_url": example_url,
                    "model_type": m.type or [],
                    "provider": getattr(m, "provider", "") or "",
                })
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
    # 409-Konflikte bei Deploy/Restart: TeleBot loggt sonst jeden Polling-Loop als ERROR
    logging.getLogger("TeleBot").setLevel(logging.WARNING)
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

    # SCHRITT G: Bot starten (mit Retry bei Timeout/409-Konflikt)
    logger.info("Bot ist bereit (Umgebung: %s)", config.APP_ENV)

    # Webhook entfernen (falls aktiv) – sonst 409 bei getUpdates
    try:
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook entfernt (falls vorhanden).")
    except Exception as e:
        logger.warning("delete_webhook fehlgeschlagen (nicht kritisch): %s", e)

    # Initiale Wartezeit: alte Instanz (Deploy/Restart) soll getUpdates freigeben
    poll_delay = int(os.getenv("TELEGRAM_POLL_START_DELAY", "25"))
    if poll_delay > 0:
        logger.info("Warte %ds vor erstem Polling (alte Instanz freigeben)...", poll_delay)
        time.sleep(poll_delay)

    retry_delay_409 = int(os.getenv("TELEGRAM_409_RETRY_DELAY", "30"))
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
                    retry_delay_409, e,
                )
                time.sleep(retry_delay_409)
            else:
                logger.critical("Kritischer Absturz: %s", e)
                sys.exit(1)


if __name__ == "__main__":
    main()