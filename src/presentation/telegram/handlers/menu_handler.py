"""
menu_handler.py – Navigation und WebApp-Aktionen (Telegram Controller).

Dieser Handler verbindet die React Mini App (WebApp) mit dem Telegram-Bot:
- Für `commands`/`keyboard`: baut er Inline-/Reply-Menüs und Navigationsschritte
- Für `webapp`-Modus: erstellt WebApp-Buttons mit URL-Pfaden wie `/webapp?path=...`
- Für WebApp-Aktionen: `process_webapp_action(...)` wird vom Flask-Endpoint `/api/webapp_action` aufgerufen
  und triggert dann den eigentlichen Generierungs-Flow über `runner.run_generation`.

Unified-Prinzip:
- Diese Datei kennt keine Provider-Details.
- Inferenz/Provider-Mapping passiert nur in `GenerationService` + `UnifiedAIClient`.
"""

import asyncio
import logging
import os

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from src.config.settings import config
from src.presentation.telegram.runtime import run_coroutine_sync
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.chat_debounce import cancel_pending_batch
from src.presentation.telegram.handlers.common import clear_context, get_context, set_context
from src.presentation.telegram.handlers.group_handler import get_group_menu_markup
from src.presentation.telegram.handlers.gen import ctx_media_to_list
from src.presentation.telegram.handlers.gen.media_helpers import schema_requires_media
from src.presentation.telegram.handlers.gen.nav_handlers import send_model_detail_view
from src.presentation.telegram.handlers.gen.start_handler import do_start_gen_flow
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.presentation.telegram.welcome_utils import send_welcome_with_video
from src.utils.strings import get_text, get_welcome

logger = logging.getLogger(__name__)


def _reset_webapp_state_unless_pending_telegram_media(user_id: int, db) -> None:
    """Wie früher am Anfang jeder WebApp-Aktion: Kontext leeren, Chat-Modus aus, Batches abbrechen.
    Ausnahme: User hat gerade ein Medium in Telegram hochgeladen und soll in der WebApp ein Modell wählen —
    dann Context mit lokalen `media_paths` behalten."""
    ctx = get_context(user_id)
    if ctx.get("step") == "waiting_for_model_for_media" and ctx.get("media_paths"):
        return
    clear_context(user_id)
    db.set_user_chat_mode(user_id, None, active=False)
    cancel_pending_batch(user_id)


def _merge_stored_telegram_media_paths(media_paths: list, user_id: int) -> None:
    """Ergänzt `media_paths` aus dem Telegram-Kontext (lokale Temp-Dateien), wenn die WebApp keine Bild-URLs liefert."""
    pre = get_context(user_id) or {}
    extra = pre.get("media_paths") or []
    if not extra:
        return
    seen: set[str] = set()
    for m in media_paths:
        if isinstance(m, dict) and m.get("path"):
            seen.add(str(m["path"]))
    for item in extra:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        if not p or str(p) in seen:
            continue
        ps = str(p)
        if ps.startswith("http://") or ps.startswith("https://"):
            media_paths.append({"path": ps, "type": item.get("type") or "image"})
            seen.add(ps)
        elif os.path.isfile(ps):
            media_paths.append({"path": ps, "type": item.get("type") or "image"})
            seen.add(ps)


def _parse_admin_id() -> int:
    raw = os.getenv("ADMIN_ID", "0") or "0"
    try:
        return int(raw.strip())
    except (ValueError, TypeError):
        return 0


ADMIN_ID = _parse_admin_id()
REFERRAL_REWARD = config.REFERRAL_REWARD
_MAX_WEBAPP_PROMPT_LEN = config._MAX_WEBAPP_PROMPT_LEN

# Wird von gen_handler.register gesetzt, damit WebApp-API (main.py) sofort generieren kann.
_webapp_run_generation = None


def set_webapp_run_generation(run_generation_fn) -> None:
    """Bindet run_generation aus runner.py für process_webapp_action (start_gen mit Prompt)."""
    global _webapp_run_generation
    _webapp_run_generation = run_generation_fn


def _trim_webapp_prompt(raw) -> str:
    if not isinstance(raw, str):
        return ""
    s = raw.strip()
    if len(s) > _MAX_WEBAPP_PROMPT_LEN:
        return s[:_MAX_WEBAPP_PROMPT_LEN]
    return s


def _is_keyboard_mode(db) -> bool:
    return db.get_bot_setting("menu_mode", "commands") == "keyboard"


def _is_webapp_mode(db) -> bool:
    return db.get_bot_setting("menu_mode", "commands") == "webapp"


def _remove_reply_keyboard_silently(facade, user_id: int) -> None:
    """Entfernt die Reply-Tastatur ohne sichtbare Punkt-Nachricht. Telegram verlangt
    mind. 1 Zeichen – wir senden, entfernen die Tastatur und löschen die Nachricht direkt."""
    remove_kbd = ReplyKeyboardRemove()
    try:
        sent = facade.send_message_sync(user_id, ".", reply_markup=remove_kbd)
        facade.delete_message_sync(user_id, sent.message_id)
    except Exception:
        pass


def _run_gen_from_webapp(run_fn, *args, **kwargs) -> None:
    if run_fn is None:
        return
    if asyncio.iscoroutinefunction(run_fn):
        return run_coroutine_sync(run_fn(*args, **kwargs), timeout=600)
    else:
        return run_fn(*args, **kwargs)


def process_webapp_action(
    facade,
    user_id: int,
    action: str,
    db,
    is_group: bool = False,
    payload: dict | None = None,
) -> dict | None:
    """Führt eine Web-App-Aktion aus. Nutzbar von web_app_data-Handler und API.
    Bei is_group=True (Gruppenchat): nur Credits + Sprache, kein volles Menü."""
    # WebApp-Aktionen laufen in dieser Reihenfolge:
    # HTTP-Endpoint (`/api/webapp_action`) -> process_webapp_action -> optional `run_generation` (via `_webapp_run_generation`)
    # -> `GenerationService` -> `UnifiedAIClient` (Provider-Mapping).
    if is_group:
        text, markup = get_group_menu_markup(db, user_id, "")
        facade.send_message_sync(user_id, text, reply_markup=markup, parse_mode="HTML")
        return

    def _send_generation_started_notice() -> None:
        try:
            facade.send_message_sync(user_id, get_text("webapp_generation_started", lang))
        except Exception:
            pass
    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]
    lang = get_lang(user_id)
    all_models = db.get_all_models()
    _reset_webapp_state_unless_pending_telegram_media(user_id, db)
    webapp_only_markup = None
    app_url = (config.APP_URL or "").strip().rstrip("/")
    if app_url.startswith("https://"):
        webapp_url = app_url + "/webapp"
        try:
            webapp_only_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=get_text("menu_mode_webapp", lang),
                            web_app=WebAppInfo(url=webapp_url),
                        )
                    ]
                ]
            )
        except Exception as e:
            logger.warning("WebApp-Markup (process_webapp_action) fehlgeschlagen: %s", e)
    if action == "nav_main":
        # Startseite der Mini App: Begrüßung + initiales Modellmenü (oder WebApp-Button).
        user_name = getattr(db, "get_user_username_or_name", lambda u: None)(user_id) or ""
        welcome_text = get_welcome(lang, user_name)
        markup = webapp_only_markup or keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
        run_coroutine_sync(send_welcome_with_video(facade, user_id, welcome_text, markup))
        _remove_reply_keyboard_silently(facade, user_id)
    elif action.startswith("nav_path_"):
        target_path = action.replace("nav_path_", "")
        title_key = f"title_{target_path.replace('/', '_')}"
        title_text = get_text(title_key, lang)
        if title_text == title_key:
            cat_name = target_path.split("/")[-1].capitalize()
            display_name = get_text(f"menu_{cat_name.lower()}", lang)
            title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
        if webapp_only_markup:
            from urllib.parse import quote

            path_url = app_url + "/webapp?path=" + quote(target_path, safe="")
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=get_text("menu_mode_webapp", lang),
                            web_app=WebAppInfo(url=path_url),
                        )
                    ]
                ]
            )
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)
        facade.send_message_sync(user_id, title_text, reply_markup=markup, parse_mode="HTML")
        _remove_reply_keyboard_silently(facade, user_id)
    elif action.startswith("sel_"):
        model_key = action.replace("sel_", "")
        if webapp_only_markup:
            from urllib.parse import quote
            model = db.get_model_by_key(model_key)
            model_name = model.name if model else model_key
            model_url = app_url + "/webapp?model=" + quote(model_key, safe="")
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=get_text("menu_mode_webapp", lang),
                            web_app=WebAppInfo(url=model_url),
                        )
                    ]
                ]
            )
            text = get_text("webapp_open_model", lang).format(name=model_name)
            facade.send_message_sync(user_id, text, reply_markup=markup, parse_mode="HTML")
            _remove_reply_keyboard_silently(facade, user_id)
        else:
            run_coroutine_sync(send_model_detail_view(facade, user_id, model_key, db, get_lang))
    elif action.startswith("start_gen_"):
        # Start der Generierung:
        # - `start_gen_<model_key>`: WebApp übergibt Modell-Key und Prompt/Optionen
        # - wir extrahieren Media-URIs aus `generation_options` und starten den gen-Flow
        #
        # Warum so:
        # - Im WebApp-UI werden Bild-Inputs oft als HTTPS-URLs in Felder wie `reference_images` / `input_image` gesendet.
        # - Für den Telegram-Flow und `UnifiedAIClient` brauchen wir daraus eine einheitliche `media_paths`-Liste.
        # - Danach reicht `GenerationService` den Prompt + `media_files` an den Provider weiter.
        model_key = action.replace("start_gen_", "")
        model = db.get_model_by_key(model_key)
        pl = payload if isinstance(payload, dict) else {}
        options: dict = {}
        raw_opts = pl.get("generation_options")
        if isinstance(raw_opts, dict):
            options = dict(raw_opts)
        neg = pl.get("negative_prompt")
        if isinstance(neg, str) and neg.strip():
            options["negative_prompt"] = neg.strip()
        prompt_trim = _trim_webapp_prompt(pl.get("prompt"))

        # WebApp sendet Bild-Inputs typischerweise in `generation_options` als URI-Felder
        # (z.B. `reference_images`, `input_image` ...). Für den Telegram-Flow und
        # die UnifiedAIClient-Datei-Zuordnung brauchen wir daraus `media_paths`.
        media_paths: list = []
        media_keys_used: set[str] = set()

        def _maybe_add_image_uri(val) -> None:
            if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                media_paths.append({"path": val, "type": "image"})
            elif isinstance(val, list):
                for x in val:
                    _maybe_add_image_uri(x)

        schema_props: dict = {}
        if model and getattr(model, "input_schema", None) and isinstance(model.input_schema, dict):
            raw_props = model.input_schema.get("properties")
            if isinstance(raw_props, dict):
                schema_props = raw_props

        # Reihenfolge wie im Replicate-Schema (x-order), z. B. image → last_frame_image
        media_rows: list[tuple[int, str, object]] = []
        for k, v in list(options.items()):
            kl = str(k).lower()
            # Nur Media-ähnliche Keys (damit wir z.B. aspect_ratio nicht anfassen).
            if (
                "image" in kl
                or "img" in kl
                or "mask" in kl
                or "frame" in kl
                or "input_reference" in kl
                or "inputreference" in kl
                or kl in ("reference_images",)
            ):
                if v:
                    prop = schema_props.get(k, {}) if isinstance(schema_props, dict) else {}
                    try:
                        x_order = int(prop.get("x-order", 999))
                    except (TypeError, ValueError):
                        x_order = 999
                    media_rows.append((x_order, k, v))
                    media_keys_used.add(k)

        media_rows.sort(key=lambda t: (t[0], str(t[1])))
        for _xo, _k, v in media_rows:
            _maybe_add_image_uri(v)

        # Entferne die URI-Keys aus generation_options, weil UnifiedAIClient sie via
        # media_files bereits über das Replicate-Schema korrekt mappen soll.
        #
        # Ergebnis:
        # - `options` enthält nur noch echte Laufzeitoptionen (duration, resolution, negative_prompt, ...).
        # - `media_paths` enthält nur noch echte Medien-Inputs.
        if media_keys_used:
            options = {k: v for k, v in options.items() if k not in media_keys_used}

        _merge_stored_telegram_media_paths(media_paths, user_id)

        # Media-Decision:
        # - `schema_requires_media(...)` schaut in das Modell-Input-Schema (aus DB),
        #   ob der Provider wirklich ein Bild/Video erwartet.
        # - `has_media` prüft, ob die WebApp tatsächlich schon Media-URIs übergeben hat.
        needs_media = bool(model and schema_requires_media(model.input_schema, model=model))
        has_media = bool(media_paths)
        run_fn = _webapp_run_generation

        # Fast-Path: Wenn wir genug Inputs haben, generieren wir sofort.
        # - `run_fn` ist über `set_webapp_run_generation(...)` gesetzt (aus runner/create_run_generation),
        #   damit wir im HTTP-Flow (Flask) denselben Codepfad nutzen wie im Telegram-Flow.
        if prompt_trim and run_fn and model and model.is_active and (has_media or not needs_media):
            ctx_pre = {
                "model_key": model_key,
                "generation_options": options,
                "media_paths": media_paths,
                "menu_path": model.menu_path or "root",
            }
            set_context(user_id, ctx_pre)
            _send_generation_started_notice()
            gen_out = _run_gen_from_webapp(
                run_fn, user_id, model_key, prompt_trim, ctx_media_to_list(ctx_pre), is_chat=False
            )
            _remove_reply_keyboard_silently(facade, user_id)
            if isinstance(gen_out, dict):
                return {"webapp_generation": gen_out}
            return

        if options or media_paths:
            existing = {
                "generation_options": options,
                "media_paths": media_paths,
            }
            set_context(user_id, existing)
        pending = prompt_trim if (needs_media and not has_media and prompt_trim) else None
        _remove_reply_keyboard_silently(facade, user_id)
        run_coroutine_sync(
            do_start_gen_flow(facade, user_id, model_key, db, get_lang, edit_message_id=None, pending_webapp_prompt=pending)
        )
    elif action.startswith("chat_mode_yes_"):
        # WebApp: Chat-Modus aktivieren (Text-LLM mit persistenter Historie).
        # Danach wird ein erster Prompt (falls vorhanden) als `chat_history_mode="once_off"`
        # angestoßen, weil der User-Start in der History bereits im Telegram Flow vorbehandelt werden kann.
        model_key = action.replace("chat_mode_yes_", "")
        model = db.get_model_by_key(model_key)
        if model and model.is_active:
            _remove_reply_keyboard_silently(facade, user_id)
            db.set_user_chat_mode(user_id, model_key, active=True)
            final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            text = get_text("chat_active_msg", lang).format(model=model.name, cost=final_cost)
            markup = keyboards.get_chat_active_menu(lang)
            facade.send_message_sync(user_id, text, reply_markup=markup, parse_mode="HTML")
            pl = payload if isinstance(payload, dict) else {}
            prompt_trim = _trim_webapp_prompt(pl.get("prompt"))
            if prompt_trim and _webapp_run_generation:
                user_name = getattr(db, "get_user_username_or_name", lambda _u: None)(user_id) or "User"
                _send_generation_started_notice()
                gen_out = _run_gen_from_webapp(
                    _webapp_run_generation,
                    user_id,
                    model_key,
                    prompt_trim,
                    None,
                    is_chat=True,
                    chat_history_mode="once_off",
                    chat_user_name=user_name,
                )
                if isinstance(gen_out, dict):
                    return {"webapp_generation": gen_out}
    elif action.startswith("chat_mode_no_"):
        # WebApp: Chat-Modus deaktivieren (falls User gerade im Chat-Flow war).
        # Danach laufen wir wieder in den normalen Generierungs-Flow.
        model_key = action.replace("chat_mode_no_", "")
        model = db.get_model_by_key(model_key)
        pl = payload if isinstance(payload, dict) else {}
        prompt_trim = _trim_webapp_prompt(pl.get("prompt"))
        _remove_reply_keyboard_silently(facade, user_id)
        if prompt_trim and _webapp_run_generation and model and model.is_active:
            merged_media: list = []
            _merge_stored_telegram_media_paths(merged_media, user_id)
            ctx_pre = {
                "model_key": model_key,
                "generation_options": {},
                "media_paths": merged_media,
                "menu_path": model.menu_path or "root",
            }
            set_context(user_id, ctx_pre)
            user_name = getattr(db, "get_user_username_or_name", lambda _u: None)(user_id) or "User"
            _send_generation_started_notice()
            gen_out = _run_gen_from_webapp(
                _webapp_run_generation,
                user_id,
                model_key,
                prompt_trim,
                ctx_media_to_list(ctx_pre),
                is_chat=False,
                chat_history_mode="once_off",
                chat_user_name=user_name,
            )
            if isinstance(gen_out, dict):
                return {"webapp_generation": gen_out}
            return
        run_coroutine_sync(do_start_gen_flow(facade, user_id, model_key, db, get_lang, edit_message_id=None))
    elif action == "cmd_shop":
        if webapp_only_markup:
            shop_url = app_url + "/webapp?view=shop"
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=get_text("menu_mode_webapp", lang),
                            web_app=WebAppInfo(url=shop_url),
                        )
                    ]
                ]
            )
            text = get_text("webapp_open_shop", lang)
            facade.send_message_sync(user_id, text, reply_markup=markup, parse_mode="HTML")
            _remove_reply_keyboard_silently(facade, user_id)
        else:
            fake = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            run_coroutine_sync(show_shop_logic(facade, fake, db, lang))
    elif action.startswith("set_lang_"):
        new_lang = action.replace("set_lang_", "")
        if new_lang in ("de", "en", "ru", "kk"):
            db.update_setting(user_id, "language", new_lang)
    elif action == "toggle_opt":
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings.get("auto_opt", True) else 1
        db.update_setting(user_id, "auto_opt", new_val)
    elif action == "toggle_daily":
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings.get("daily_msg", True) else 1
        db.update_setting(user_id, "daily_msg", new_val)
    elif action == "optimize_prompt_paid":
        # WebApp: Bezahlt 3 Credits (in UI als 3 ⭐ angezeigt) für eine Gemini-Prompt-Optimierung.
        pl = payload if isinstance(payload, dict) else {}
        raw_prompt = pl.get("prompt")
        prompt_trim = _trim_webapp_prompt(raw_prompt)
        if not prompt_trim:
            raise ValueError("missing_prompt")

        opt_cost = 3
        current_credits = int(db.get_user_credits(user_id))
        if current_credits < opt_cost:
            raise ValueError("Zu wenig Guthaben für Prompt-Optimierung (3 Credits).")

        db.update_credits(user_id, -opt_cost, reason="prompt_optimize")

        from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm

        optimized = optimize_prompt_via_llm(prompt_trim)
        new_credits = int(db.get_user_credits(user_id))
        return {"optimized_prompt": optimized, "credits": new_credits}
    elif action.startswith("buy_credits_"):
        parts = action.replace("buy_credits_", "").split("_")
        if len(parts) >= 2:
            try:
                credits = int(parts[0])
                price = int(parts[1])
                from src.presentation.telegram.handlers.payment_handler import send_invoice_to_user

                run_coroutine_sync(send_invoice_to_user(facade, user_id, credits, price, lang))
            except (ValueError, IndexError) as e:
                logger.warning("Invalid buy_credits action %r: %s", action, e)


def register(router, facade, generation_service, db, daily_service=None) -> None:
    from src.presentation.telegram.handlers.menu_register_impl import register_menu_handlers

    register_menu_handlers(router, facade, generation_service, db, daily_service=daily_service)

