"""
Flask-Routen für Healthcheck, React-Mini-App und JSON-APIs der Web-App.

Die laufende App hält DB- und Bot-Referenzen in einem gemeinsamen Runtime-Objekt
(siehe `main.app_runtime`), damit `main.py` schlank bleibt und Tests das Objekt
patchen können.
"""
from __future__ import annotations

import io
import logging
import os
import threading
import time
from typing import Any

from flask import Flask, jsonify, redirect, request, send_from_directory

from src.config.settings import config

logger = logging.getLogger(__name__)

# --- Lightweight API rate limiting (in-memory, process-local) ---
_rate_lock = threading.Lock()
_rate_hits: dict[tuple[str, str], list[float]] = {}


def _client_ip() -> str:
    # Hinter Proxies zuerst X-Forwarded-For beachten.
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if xff:
        return xff.split(",")[0].strip()
    return (request.remote_addr or "unknown").strip()


def _rate_limited(bucket: str, key: str, max_requests: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - max(1, int(window_seconds))
    bk = (bucket, key)
    with _rate_lock:
        arr = _rate_hits.get(bk, [])
        if arr:
            arr = [ts for ts in arr if ts >= cutoff]
        arr.append(now)
        _rate_hits[bk] = arr
        # Opportunistisches Cleanup alter Buckets.
        if len(_rate_hits) > 5000:
            dead_keys = [k for k, v in _rate_hits.items() if not v or v[-1] < cutoff]
            for dk in dead_keys[:1000]:
                _rate_hits.pop(dk, None)
        return len(arr) > max_requests


def _too_many_requests(message: str = "rate_limited", retry_after_sec: int = 10):
    body = jsonify(ok=False, error=message)
    return body, 429, {"Retry-After": str(max(1, int(retry_after_sec)))}


class AppRuntime:
    """Von `main` gesetzte Referenzen für HTTP-Handler (kein globaler Zustand über Modulgrenzen)."""

    __slots__ = ("db", "bot", "generation_service", "bot_username")

    def __init__(self) -> None:
        self.db: Any = None
        self.bot: Any = None
        self.generation_service: Any = None
        # Einmal beim Bot-Start gesetzt — vermeidet get_me_sync() pro WebApp-Request (Waitress-Thread
        # würde sonst auf den Telegram-Event-Loop warten; bei langen AI-News-Sendungen: Stau/Timeouts → UI zeigt 0 Credits).
        self.bot_username: str = ""


def _webapp_react_dist_dir(project_root: str) -> str:
    return os.path.join(project_root, "webapp-react", "dist")


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


def _replicate_file_url(resp) -> str | None:
    url = getattr(resp, "url", None)
    if not url and hasattr(resp, "urls") and isinstance(resp.urls, dict):
        url = resp.urls.get("get")
    return str(url) if url else None


def register_flask_routes(app: Flask, runtime: AppRuntime, *, project_root: str) -> None:
    """
    Registriert alle HTTP-Endpunkte.

    Wichtige Prinzipien:
    - Keine globalen DB/Bot-Variablen: stattdessen `runtime.db` und `runtime.bot`.
    - Endpunkte sind bewusst defensiv (bei fehlendem DB/Bot liefern sie einen klaren Fehler).
    - React Mini-App (Vite) wird als statische Datei-Assets ausgeliefert,
      JSON-Endpunkte liefern Daten für den React Flow.
    """

    rate_window = max(1, int(os.getenv("HTTP_RATE_LIMIT_WINDOW_SECONDS", "10")))
    ip_limit_general = max(10, int(os.getenv("HTTP_RATE_LIMIT_MAX_REQUESTS_PER_IP", "180")))
    ip_limit_heavy = max(5, int(os.getenv("HTTP_RATE_LIMIT_MAX_REQUESTS_PER_IP_HEAVY", "50")))
    user_limit_actions = max(5, int(os.getenv("HTTP_RATE_LIMIT_MAX_REQUESTS_PER_USER", "45")))

    @app.before_request
    def _global_rate_limit_guard():
        path = request.path or "/"
        if not path.startswith("/api/"):
            return None
        ip = _client_ip()
        # Allgemeines API-Limit.
        if _rate_limited("ip:all", ip, ip_limit_general, rate_window):
            return _too_many_requests("rate_limited_ip", retry_after_sec=rate_window)
        # Schärferes Limit für teure Endpunkte.
        heavy = (
            path.startswith("/api/webapp_action")
            or path.startswith("/api/webapp_upload_reference")
            or path.startswith("/api/user_info")
            or path.startswith("/api/models")
            or path.startswith("/api/model")
        )
        if heavy and _rate_limited("ip:heavy", f"{ip}:{path}", ip_limit_heavy, rate_window):
            return _too_many_requests("rate_limited_heavy", retry_after_sec=rate_window)
        return None

    @app.route("/")
    def health_check():
        return "🤖 System Status: ONLINE", 200

    @app.route("/webapp")
    def webapp():
        """Telegram Mini App – React (Vite-Build unter webapp-react/dist)."""
        dist_dir = _webapp_react_dist_dir(project_root)
        index_path = os.path.join(dist_dir, "index.html")
        if not os.path.isfile(index_path):
            return (
                "<h1>Web App Build nicht gefunden</h1><p>Führe <code>npm run build --prefix webapp-react</code> aus.</p>",
                404,
                {"Content-Type": "text/html; charset=utf-8"},
            )
        return send_from_directory(dist_dir, "index.html")

    @app.route("/webapp/<path:filename>")
    def webapp_assets(filename: str):
        """Statische Assets aus dem Vite-Output (z. B. /webapp/assets/…)."""
        dist_dir = _webapp_react_dist_dir(project_root)
        try:
            resp = send_from_directory(dist_dir, filename)
            # Aggressiver Cache für hash-basierten Build-Output -> schnelleres TTI.
            if "/assets/" in f"/{filename}":
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return resp
        except Exception:
            return "", 404

    @app.route("/webapp-react")
    @app.route("/webapp-react/")
    def webapp_react_legacy_redirect():
        """Alte BotFather-URLs; einheitlich /webapp/."""
        return redirect("/webapp", code=308)

    @app.route("/webapp-react/<path:filename>")
    def webapp_react_legacy_assets_redirect(filename: str):
        return redirect(f"/webapp/{filename}", code=308)

    @app.route("/api/webapp_action", methods=["POST"])
    def api_webapp_action():
        """Web-App: Aktionen per POST (sendData greift am Menü-Button nicht)."""
        if runtime.db is None:
            return jsonify(ok=False, error="no_db"), 400
        try:
            from src.utils.telegram_init_data import validate_init_data
            from src.presentation.telegram.handlers.menu_handler import process_webapp_action, _is_webapp_mode

            data = request.get_json() or {}
            action = data.get("action", "")
            init_data = data.get("init_data", "")
            if not action or not init_data:
                return jsonify(ok=False, error="missing_params"), 400
            if not _is_webapp_mode(runtime.db):
                return jsonify(ok=False, error="webapp_disabled"), 400

            user_id = validate_init_data(init_data, config.TELEGRAM_TOKEN)
            if not user_id:
                return jsonify(ok=False, error="invalid_init_data"), 403
            if _rate_limited("uid:webapp_action", str(user_id), user_limit_actions, rate_window):
                return _too_many_requests("rate_limited_user", retry_after_sec=rate_window)

            if runtime.bot is None:
                return jsonify(ok=False, error="no_bot"), 500

            res_data = process_webapp_action(runtime.bot, user_id, action, runtime.db, payload=data)
            if res_data is None:
                return jsonify(ok=True)
            return jsonify(ok=True, **res_data)
        except ValueError as e:
            logger.info("webapp_action validation error: %s", e)
            return jsonify(ok=False, error=str(e)), 400
        except Exception as e:
            logger.exception("webapp_action error: %s", e)
            return jsonify(ok=False, error="internal_error"), 500

    @app.route("/api/user_info", methods=["POST"])
    def api_user_info():
        """Web-App: Nutzerinfos via init_data."""
        if runtime.db is None:
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
            if _rate_limited("uid:user_info", str(user_id), user_limit_actions, rate_window):
                return _too_many_requests("rate_limited_user", retry_after_sec=rate_window)

            user = runtime.db.get_user(user_id)
            settings = runtime.db.get_user_settings(user_id)
            credits = runtime.db.get_user_credits(user_id)
            bot_username = (getattr(runtime, "bot_username", None) or "").strip()
            return jsonify(
                ok=True,
                user_id=user_id,
                username=user.username or "User",
                credits=credits,
                lang=settings["lang"],
                auto_opt=bool(settings.get("auto_opt", True)),
                daily_msg=bool(settings.get("daily_msg", True)),
                bot_username=bot_username,
            )
        except Exception as e:
            logger.exception("api_user_info error: %s", e)
            return jsonify(ok=False, error="internal_error"), 500

    @app.route("/api/strings")
    def api_strings():
        lang = request.args.get("lang", "de") or "de"
        if lang not in ("de", "en", "ru", "kk"):
            lang = "de"
        try:
            from src.utils.strings import get_webapp_strings

            return jsonify(get_webapp_strings(lang))
        except Exception as e:
            logger.warning("api_strings error: %s", e)
            return jsonify({}), 200

    @app.route("/api/legal")
    def api_legal():
        """WebApp: Datenschutz + Impressum (Texte aus src/legal/, nicht strings.py)."""
        lang = request.args.get("lang", "de") or "de"
        if lang not in ("de", "en", "ru", "kk"):
            lang = "de"
        try:
            from src.legal import (
                build_imprint_placeholders,
                build_privacy_context,
                render_impressum,
                render_privacy,
                webapp_legal_labels,
            )

            im_ctx = build_imprint_placeholders(config, lang)
            pr_ctx = build_privacy_context(config)
            return jsonify(
                ok=True,
                lang=lang,
                privacy=render_privacy(lang, pr_ctx),
                impressum=render_impressum(lang, im_ctx),
                labels=webapp_legal_labels(lang),
            )
        except Exception as e:
            logger.exception("api_legal error: %s", e)
            return jsonify(ok=False, error="internal_error"), 500

    @app.route("/api/model")
    def api_model():
        if runtime.db is None:
            return jsonify(ok=False, error="no_db"), 400
        key = request.args.get("key", "")
        if not key:
            return jsonify(ok=False, error="missing_key"), 400
        try:
            model = runtime.db.get_model_by_key(key)
            if not model or not model.is_active:
                return jsonify(ok=False, error="not_found"), 404
            final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            replicate_id = model.replicate_id or ""
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

            return jsonify(
                ok=True,
                key=model.key,
                name=model.name,
                description=model.description or "",
                example_image_url=example_url,
                example_prompt=example_prompt,
                final_cost=final_cost,
                menu_path=model.menu_path or "root",
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
                },
            )
        except Exception as e:
            logger.warning("api_model error: %s", e)
            return jsonify(ok=False, error="internal_error"), 500

    @app.route("/api/webapp_upload_reference", methods=["POST"])
    def api_webapp_upload_reference():
        # Für Video/Audio-Workflows höheres Limit als reine Bild-Uploads.
        max_bytes = 80 * 1024 * 1024
        max_files = 10
        allowed_mime = frozenset(
            {
                # Images
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/heic",
                "image/heif",
                "image/bmp",
                "image/gif",
                # Video
                "video/mp4",
                "video/quicktime",
                "video/webm",
                "video/x-msvideo",
                "video/x-matroska",
                "video/mp2t",
                # Audio
                "audio/mpeg",
                "audio/wav",
                "audio/x-wav",
                "audio/mp4",
                "audio/aac",
                "audio/ogg",
                "audio/flac",
                "audio/webm",
            }
        )

        if runtime.db is None:
            return jsonify(ok=False, error="no_db"), 400
        try:
            import replicate
            from src.utils.telegram_init_data import validate_init_data
            from src.presentation.telegram.handlers.menu_handler import _is_webapp_mode

            init_data = request.form.get("init_data", "")
            if not init_data:
                return jsonify(ok=False, error="missing_init_data"), 400
            if not _is_webapp_mode(runtime.db):
                return jsonify(ok=False, error="webapp_disabled"), 400

            user_id = validate_init_data(init_data, config.TELEGRAM_TOKEN)
            if not user_id:
                return jsonify(ok=False, error="invalid_init_data"), 403
            if _rate_limited("uid:upload", str(user_id), max(3, user_limit_actions // 2), rate_window):
                return _too_many_requests("rate_limited_upload", retry_after_sec=rate_window)

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
                if ext in (".heic", ".heif"):
                    return "image/heic"
                if ext == ".bmp":
                    return "image/bmp"
                if ext == ".gif":
                    return "image/gif"
                if ext in (".mp4", ".m4v"):
                    return "video/mp4"
                if ext == ".mov":
                    return "video/quicktime"
                if ext == ".webm":
                    # webm kann Audio oder Video enthalten; serverseitig ist beides erlaubt.
                    return "video/webm"
                if ext == ".avi":
                    return "video/x-msvideo"
                if ext == ".mkv":
                    return "video/x-matroska"
                if ext == ".mp3":
                    return "audio/mpeg"
                if ext == ".wav":
                    return "audio/wav"
                if ext in (".m4a", ".aac"):
                    return "audio/aac"
                if ext == ".ogg":
                    return "audio/ogg"
                if ext == ".flac":
                    return "audio/flac"
                return ""

            # Replicate Files API → URLs für Model-Input (s. Input files in der Doku):
            # https://replicate.com/docs/topics/predictions/input-files
            client = replicate.Client(api_token=config.REPLICATE_API_TOKEN)
            urls: list[str] = []

            for fs in files:
                raw = fs.read()
                if len(raw) > max_bytes:
                    return jsonify(ok=False, error="file_too_large"), 400
                mime = _mime_for_upload(fs)
                if mime not in allowed_mime:
                    return jsonify(ok=False, error="invalid_type"), 400
                fn = os.path.basename(fs.filename or "upload.bin") or "upload.bin"
                resp = client.files.create(file=io.BytesIO(raw), filename=fn, type=mime)
                url = _replicate_file_url(resp)
                if not url or not (url.startswith("http://") or url.startswith("https://")):
                    return jsonify(ok=False, error="upload_failed"), 500
                urls.append(url)

            return jsonify(ok=True, urls=urls)
        except Exception as e:
            logger.exception("webapp_upload_reference error: %s", e)
            return jsonify(ok=False, error="internal_error"), 500

    @app.route("/api/shop_packages")
    def api_shop_packages():
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

    @app.route("/api/models")
    def api_models():
        if runtime.db is None:
            return jsonify(models=[], folders=[], title=""), 200
        path = request.args.get("path", "root") or "root"
        try:
            models = runtime.db.get_all_models()
            sub_cats: set[str] = set()
            items = []
            favorites_items = []
            path_str = str(path or "root")
            top_category = path_str.split("/")[0] if path_str != "root" else ""

            def _is_under_image_tree(menu_path: str) -> bool:
                mp = str(menu_path or "")
                return mp == "image" or mp.startswith("image/")

            def _belongs_to_view(m) -> bool:
                mp = str(getattr(m, "menu_path", "") or "")
                return mp == path_str

            def _belongs_to_top_category(m) -> bool:
                if not top_category:
                    return False
                mp = str(getattr(m, "menu_path", "") or "")
                return mp == top_category or mp.startswith(top_category + "/")

            for m in models:
                if _belongs_to_view(m):
                    cost = int(m.custom_price if m.custom_price is not None else m.internal_cost)
                    example_url = _resolve_example_url(getattr(m, "example_data", None))
                    items.append(
                        {
                            "key": m.key,
                            "name": m.name,
                            "final_cost": cost,
                            "is_favorite": bool(getattr(m, "is_favorite", False)),
                            "example_image_url": example_url,
                            "model_type": m.type or [],
                            "provider": getattr(m, "provider", "") or "",
                        }
                    )
                if bool(getattr(m, "is_favorite", False)) and _belongs_to_top_category(m):
                    fav_cost = int(m.custom_price if m.custom_price is not None else m.internal_cost)
                    fav_example_url = _resolve_example_url(getattr(m, "example_data", None))
                    favorites_items.append(
                        {
                            "key": m.key,
                            "name": m.name,
                            "final_cost": fav_cost,
                            "is_favorite": True,
                            "example_image_url": fav_example_url,
                            "model_type": m.type or [],
                            "provider": getattr(m, "provider", "") or "",
                        }
                    )
                elif path_str == "root" and m.menu_path and m.menu_path != "root":
                    mp_root = str(m.menu_path)
                    sub_cats.add(mp_root.split("/")[0] if "/" in mp_root else mp_root)
                elif path_str in ("image", "video", "audio", "text", "tools"):
                    if str(m.menu_path or "").startswith(path_str + "/"):
                        rel = str(m.menu_path)[len(path_str) + 1 :]
                        if rel:
                            sub_cats.add(rel.split("/")[0])
                elif path_str != "root" and str(m.menu_path or "").startswith(path_str + "/"):
                    sub_cats.add(str(m.menu_path)[len(path_str) + 1 :].split("/")[0])
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
                titles = {
                    "image": "Bild Studio",
                    "video": "Video Studio",
                    "audio": "Audio Studio",
                    "text": "Text / Chat",
                    "tools": "Werkzeuge",
                }
            root_title = "Kategorien"
            try:
                from src.utils.strings import get_text

                root_title = get_text("webapp_categories", lang)
            except Exception:
                pass
            title = titles.get(path.split("/")[-1], path.replace("/", " · ").title() if path != "root" else root_title)
            sorted_sub_cats = sorted(sub_cats, key=lambda s: (0, s.lower()) if s.lower() in ("favorites", "favoriten", "favourites") else (1, s.lower()))
            folders = [{"path": seg if path == "root" else f"{path}/{seg}", "slug": seg} for seg in sorted_sub_cats]
            favorites_items = sorted(favorites_items, key=lambda x: (x.get("name") or "").lower())
            return jsonify(models=items, favorites_models=favorites_items, folders=folders, title=title)
        except Exception as e:
            logger.warning("api_models error: %s", e)
            return jsonify(models=[], favorites_models=[], folders=[], title=""), 200

    @app.route("/api/replicate_webhook", methods=["POST"])
    def replicate_webhook():
        from src.presentation.http.replicate_webhook_handler import handle_replicate_webhook_request

        return handle_replicate_webhook_request(runtime, request)
