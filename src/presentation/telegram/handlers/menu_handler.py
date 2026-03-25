import json
import logging
import os

from telebot import TeleBot, types

from src.config.settings import config
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


def _parse_admin_id() -> int:
    raw = os.getenv("ADMIN_ID", "0") or "0"
    try:
        return int(raw.strip())
    except (ValueError, TypeError):
        return 0


ADMIN_ID = _parse_admin_id()

REFERRAL_REWARD = 50

_MAX_WEBAPP_PROMPT_LEN = 12000

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


def _remove_reply_keyboard_silently(bot: TeleBot, user_id: int) -> None:
    """Entfernt die Reply-Tastatur ohne sichtbare Punkt-Nachricht. Telegram verlangt
    mind. 1 Zeichen – wir senden, entfernen die Tastatur und löschen die Nachricht direkt."""
    remove_kbd = types.ReplyKeyboardRemove(selective=False)
    try:
        sent = bot.send_message(user_id, ".", reply_markup=remove_kbd)
        bot.delete_message(user_id, sent.message_id)
    except Exception:
        pass


def process_webapp_action(
    bot: TeleBot,
    user_id: int,
    action: str,
    db,
    is_group: bool = False,
    payload: dict | None = None,
) -> dict | None:
    """Führt eine Web-App-Aktion aus. Nutzbar von web_app_data-Handler und API.
    Bei is_group=True (Gruppenchat): nur Credits + Sprache, kein volles Menü."""
    if is_group:
        text, markup = get_group_menu_markup(db, user_id, "")
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return
    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]
    lang = get_lang(user_id)
    all_models = db.get_all_models()
    clear_context(user_id)
    db.set_user_chat_mode(user_id, None, active=False)
    cancel_pending_batch(user_id)
    webapp_only_markup = None
    app_url = (config.APP_URL or "").strip().rstrip("/")
    if app_url.startswith("https://"):
        webapp_url = app_url + "/webapp"
        try:
            webapp_only_markup = types.InlineKeyboardMarkup()
            webapp_only_markup.add(types.InlineKeyboardButton(
                get_text("menu_mode_webapp", lang),
                web_app=types.WebAppInfo(url=webapp_url)
            ))
        except Exception as e:
            logger.warning("WebApp-Markup (process_webapp_action) fehlgeschlagen: %s", e)
    if action == "nav_main":
        user_name = getattr(db, "get_user_username_or_name", lambda u: None)(user_id) or ""
        welcome_text = get_welcome(lang, user_name)
        markup = webapp_only_markup or keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
        send_welcome_with_video(bot, user_id, welcome_text, markup)
        _remove_reply_keyboard_silently(bot, user_id)
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
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=path_url)))
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)
        bot.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")
        _remove_reply_keyboard_silently(bot, user_id)
    elif action.startswith("sel_"):
        model_key = action.replace("sel_", "")
        if webapp_only_markup:
            from urllib.parse import quote
            model = db.get_model_by_key(model_key)
            model_name = model.name if model else model_key
            model_url = app_url + "/webapp?model=" + quote(model_key, safe="")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=model_url)))
            text = get_text("webapp_open_model", lang).format(name=model_name)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            _remove_reply_keyboard_silently(bot, user_id)
        else:
            send_model_detail_view(bot, user_id, model_key, db, get_lang)
    elif action.startswith("start_gen_"):
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
                    _maybe_add_image_uri(v)
                    media_keys_used.add(k)

        # Entferne die URI-Keys aus generation_options, weil UnifiedAIClient sie via
        # media_files bereits über das Replicate-Schema korrekt mappen soll.
        if media_keys_used:
            options = {k: v for k, v in options.items() if k not in media_keys_used}

        needs_media = bool(model and schema_requires_media(model.input_schema, model=model))
        has_media = bool(media_paths)
        run_fn = _webapp_run_generation

        if prompt_trim and run_fn and model and model.is_active and (has_media or not needs_media):
            ctx_pre = {
                "model_key": model_key,
                "generation_options": options,
                "media_paths": media_paths,
                "menu_path": model.menu_path or "root",
            }
            set_context(user_id, ctx_pre)
            run_fn(user_id, model_key, prompt_trim, ctx_media_to_list(ctx_pre), is_chat=False)
            _remove_reply_keyboard_silently(bot, user_id)
            return

        if options or media_paths:
            existing = {
                "generation_options": options,
                "media_paths": media_paths,
            }
            set_context(user_id, existing)
        pending = prompt_trim if (needs_media and not has_media and prompt_trim) else None
        _remove_reply_keyboard_silently(bot, user_id)
        do_start_gen_flow(
            bot, user_id, model_key, db, get_lang, edit_message_id=None, pending_webapp_prompt=pending
        )
    elif action.startswith("chat_mode_yes_"):
        model_key = action.replace("chat_mode_yes_", "")
        model = db.get_model_by_key(model_key)
        if model and model.is_active:
            _remove_reply_keyboard_silently(bot, user_id)
            db.set_user_chat_mode(user_id, model_key, active=True)
            final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            text = get_text("chat_active_msg", lang).format(model=model.name, cost=final_cost)
            markup = keyboards.get_chat_active_menu(lang)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            pl = payload if isinstance(payload, dict) else {}
            prompt_trim = _trim_webapp_prompt(pl.get("prompt"))
            if prompt_trim and _webapp_run_generation:
                user_name = getattr(db, "get_user_username_or_name", lambda _u: None)(user_id) or "User"
                _webapp_run_generation(
                    user_id,
                    model_key,
                    prompt_trim,
                    None,
                    is_chat=True,
                    chat_history_mode="once_off",
                    chat_user_name=user_name,
                )
    elif action.startswith("chat_mode_no_"):
        model_key = action.replace("chat_mode_no_", "")
        model = db.get_model_by_key(model_key)
        pl = payload if isinstance(payload, dict) else {}
        prompt_trim = _trim_webapp_prompt(pl.get("prompt"))
        _remove_reply_keyboard_silently(bot, user_id)
        if prompt_trim and _webapp_run_generation and model and model.is_active:
            ctx_pre = {
                "model_key": model_key,
                "generation_options": {},
                "media_paths": [],
                "menu_path": model.menu_path or "root",
            }
            set_context(user_id, ctx_pre)
            user_name = getattr(db, "get_user_username_or_name", lambda _u: None)(user_id) or "User"
            _webapp_run_generation(
                user_id,
                model_key,
                prompt_trim,
                None,
                is_chat=False,
                chat_history_mode="once_off",
                chat_user_name=user_name,
            )
            return
        do_start_gen_flow(bot, user_id, model_key, db, get_lang, edit_message_id=None)
    elif action == "cmd_shop":
        if webapp_only_markup:
            shop_url = app_url + "/webapp?view=shop"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=shop_url)))
            text = get_text("webapp_open_shop", lang)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            _remove_reply_keyboard_silently(bot, user_id)
        else:
            fake = type('Msg', (), {'chat': type('C', (), {'id': user_id})()})()
            show_shop_logic(bot, fake, db, lang)
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
                send_invoice_to_user(bot, user_id, credits, price, lang)
            except (ValueError, IndexError) as e:
                logger.warning("Invalid buy_credits action %r: %s", action, e)


def register(bot: TeleBot, generation_service, db) -> None:
    def get_lang(user_id):
        return db.get_user_settings(user_id)["lang"]

    # 0a. ADMIN: Menü-Modus umschalten (commands | keyboard)
    @bot.message_handler(commands=['set_menu_mode'])
    def admin_set_menu_mode(message):
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            bot.reply_to(message, f"⛔ Nur für Admins. Deine ID: {user_id} – prüfe ADMIN_ID in .env")
            return
        lang = get_lang(user_id)
        parts = (message.text or "").strip().split()
        if len(parts) < 2:
            current = db.get_bot_setting("menu_mode", "commands")
            bot.reply_to(message, f"📋 Aktueller Modus: <b>{current}</b>\n\n"
                "Zum Ändern: /set_menu_mode <code>commands</code> | <code>keyboard</code> | <code>webapp</code>", parse_mode="HTML")
            return
        mode = parts[1].lower()
        if mode not in ("commands", "keyboard", "webapp"):
            bot.reply_to(message, get_text("admin_menu_mode_invalid", lang))
            return
        db.set_bot_setting("menu_mode", mode)
        hint = ""
        if mode == "keyboard":
            hint = "\n\n👇 Sende /start um die Tastatur zu sehen."
        elif mode == "webapp":
            if config.APP_URL:
                hint = "\n\n✅ Bot neu starten – dann öffnet das 🌐 neben dem Eingabefeld die App."
            else:
                hint = "\n\n⚠️ Keine HTTPS-URL. Lokal: ngrok http 5000, dann APP_URL=https://xxx.ngrok-free.app"
        bot.reply_to(message, get_text("admin_menu_mode_set", lang).format(mode=mode) + hint)

    def _should_handle_keyboard_nav(m):
        if not _is_keyboard_mode(db) or not m.text:
            return False
        if keyboards.get_keyboard_action_for_text(m.text) is not None:
            return True
        ctx = get_context(m.chat.id)
        path = ctx.get("keyboard_path")
        if path is not None:
            models = db.get_all_models()
            return keyboards.get_path_keyboard_action(m.text, path, models, get_lang(m.chat.id)) is not None
        return False

    @bot.message_handler(func=_should_handle_keyboard_nav)
    def handle_keyboard_nav(message):
        user_id = message.chat.id
        lang = get_lang(user_id)
        all_models = db.get_all_models()

        try:
            bot.delete_message(user_id, message.message_id)
        except Exception:
            pass

        action = keyboards.get_keyboard_action_for_text(message.text)
        if action is None:
            ctx = get_context(user_id)
            path = ctx.get("keyboard_path", "root")
            path_result = keyboards.get_path_keyboard_action(message.text, path, all_models, lang)
            if path_result:
                act_type, target = path_result
                if act_type == "nav_main":
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    cancel_pending_batch(user_id)
                    un = (message.from_user and message.from_user.first_name) or ""
                    welcome_text = get_welcome(lang, un)
                    markup = keyboards.get_main_reply_keyboard(lang)
                    send_welcome_with_video(bot, user_id, welcome_text, markup)
                elif act_type == "nav_path":
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    set_context(user_id, {"keyboard_path": target})
                    path_markup = keyboards.get_path_reply_keyboard(all_models, lang, target)
                    title_key = f"title_{target.replace('/', '_')}"
                    title_text = get_text(title_key, lang)
                    if title_text == title_key:
                        cat_name = target.split("/")[-1].capitalize()
                        display_name = get_text(f"menu_{cat_name.lower()}", lang)
                        title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
                    bot.send_message(user_id, title_text, reply_markup=path_markup, parse_mode='HTML')
                elif act_type == "sel":
                    prev = get_context(user_id) or {}
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    cancel_pending_batch(user_id)
                    send_model_detail_view(bot, user_id, target, db, get_lang)
                    set_context(user_id, {
                        "model_key": target,
                        "step": "viewing_model",
                        "keyboard_path": path,
                        "menu_path": path,
                        "media_paths": prev.get("media_paths") or [],
                    })
            return

        clear_context(user_id)
        db.set_user_chat_mode(user_id, None, active=False)
        cancel_pending_batch(user_id)
        if action == "nav_main":
            un = (message.from_user and message.from_user.first_name) or ""
            welcome_text = get_welcome(lang, un)
            markup = keyboards.get_main_reply_keyboard(lang)
            send_welcome_with_video(bot, user_id, welcome_text, markup)
        elif action.startswith("nav_path_"):
            target_path = action.replace("nav_path_", "")
            set_context(user_id, {"keyboard_path": target_path})
            path_markup = keyboards.get_path_reply_keyboard(all_models, lang, target_path)
            title_key = f"title_{target_path.replace('/', '_')}"
            title_text = get_text(title_key, lang)
            if title_text == title_key:
                cat_name = target_path.split("/")[-1].capitalize()
                display_name = get_text(f"menu_{cat_name.lower()}", lang)
                title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
            bot.send_message(user_id, title_text, reply_markup=path_markup, parse_mode='HTML')
        elif action == "nav_profile":
            creds = db.get_user_credits(user_id)
            text = get_text("profile_text", lang).format(
                name=message.from_user.first_name,
                creds=creds,
                user_id=user_id
            )
            markup = keyboards.get_back_menu(lang, target="nav_main")
            bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')
        elif action == "cmd_shop":
            show_shop_logic(bot, message, db, lang)

    # 0. ADMIN: Modelle aus Neon neu laden (Cache leeren)
    @bot.message_handler(commands=['reload_models'])
    def admin_reload_models(message):
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            return
        try:
            # Cache invalidieren
            if hasattr(db, "_models_cache"):
                delattr(db, "_models_cache")
            if hasattr(db, "_models_cache_ts"):
                delattr(db, "_models_cache_ts")
            # einmalig neu holen (Neon-Fetch triggern)
            models = db.get_all_models()
            bot.send_message(
                user_id,
                f"✅ Modelle neu aus Neon geladen. Anzahl: {len(models)}",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.exception("Admin reload_models failed: %s", e)
            bot.send_message(
                user_id,
                f"❌ Fehler beim Neuladen der Modelle: {e}",
                parse_mode="HTML",
            )

    # 0c. Web App Data (Mini App sendet Aktionen – funktioniert nur bei Keyboard-Button, nicht Menü-Button)
    @bot.message_handler(content_types=['web_app_data'])
    def handle_web_app_data(message):
        if not _is_webapp_mode(db):
            return
        try:
            data = json.loads(message.web_app_data.data)
            action = data.get("action", "")
        except (json.JSONDecodeError, TypeError, AttributeError):
            return
        user_id = message.chat.id
        is_group = str(message.chat.type) in ("group", "supergroup")
        try:
            bot.delete_message(user_id, message.message_id)
        except Exception:
            pass
        process_webapp_action(bot, user_id, action, db, is_group=is_group, payload=data)

    # 1. START COMMAND (nur private Chats – Gruppen werden von group_handler bedient)
    @bot.message_handler(commands=['start'], func=lambda m: str(m.chat.type) == 'private')
    def send_welcome(message):
        user_id = message.chat.id
        db.add_user_if_not_exists(user_id, message.from_user.username)
        lang = get_lang(user_id)
        
        old_ctx = get_context(user_id)
        if old_ctx and "last_bot_msg_id" in old_ctx:
            try:
                bot.delete_message(user_id, old_ctx["last_bot_msg_id"])
            except Exception:
                pass
        clear_context(user_id)

        args = message.text.split()
        if len(args) > 1 and not db.user_exists(user_id):
            try:
                ref_id = int(args[1])
                if ref_id != user_id:
                    db.update_credits(ref_id, REFERRAL_REWARD, "referral")
                    bot.send_message(
                        ref_id,
                        get_text("ref_success_referrer", get_lang(ref_id)).format(amount=REFERRAL_REWARD),
                    )
            except (ValueError, IndexError):
                pass
        else:
            # Empfehle uns lieber user
            no_referral_text = get_text("no_referral", lang)
            bot.send_message(user_id, no_referral_text, parse_mode='HTML')
        
        # Transparenz
        transparency_text = get_text("transparency_msg", lang)
        bot.send_message(user_id, transparency_text, parse_mode='HTML')


        user_name = (message.from_user and message.from_user.first_name) or ""
        welcome_text = get_welcome(lang, user_name)
        all_models = db.get_all_models()

        if _is_keyboard_mode(db):
            reply_kbd = keyboards.get_main_reply_keyboard(lang)
            send_welcome_with_video(bot, user_id, welcome_text, reply_kbd)
        elif _is_webapp_mode(db) and config.APP_URL:
            webapp_url = (config.APP_URL or "").rstrip("/")
            if webapp_url.startswith("https://"):
                webapp_url = webapp_url + "/webapp"
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        get_text("menu_mode_webapp", lang),
                        web_app=types.WebAppInfo(url=webapp_url)
                    ))
                    send_welcome_with_video(bot, user_id, welcome_text, markup)
                    _remove_reply_keyboard_silently(bot, user_id)
                except Exception as e:
                    logger.warning("WebApp-Button fehlgeschlagen, Fallback zu Inline-Menü: %s", e)
                    markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                    send_welcome_with_video(bot, user_id, welcome_text, markup)
                    _remove_reply_keyboard_silently(bot, user_id)
            else:
                markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                send_welcome_with_video(bot, user_id, welcome_text, markup)
                _remove_reply_keyboard_silently(bot, user_id)
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            send_welcome_with_video(bot, user_id, welcome_text, markup)
            _remove_reply_keyboard_silently(bot, user_id)

    # 2. NAVIGATION (Static Menus)
    # WICHTIG: Wir ignorieren hier 'nav_path_', damit gen_handler diese übernehmen kann!
    @bot.callback_query_handler(func=lambda call: call.data.startswith('nav_') and not call.data.startswith('nav_path_'))
    def handle_navigation(call):
        chat_id = call.message.chat.id
        chat_type = str(call.message.chat.type)
        if chat_type in ("group", "supergroup"):
            text, markup = get_group_menu_markup(db, chat_id, (call.from_user.first_name or call.from_user.username or "") if call.from_user else "")
            try:
                bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            return

        user_id = chat_id
        lang = get_lang(user_id)
        
        try:
            target = call.data.split('_')[1]
        except IndexError:
            return # Falls Format falsch ist
        
        new_text = ""
        new_markup = None
        
        if target == "main":
            user_name = db.get_user_username_or_name(user_id) or ""
            new_text = get_welcome(lang, user_name)
            all_models = db.get_all_models()
            clear_context(user_id)
            if _is_keyboard_mode(db):
                main_kbd = keyboards.get_main_reply_keyboard(lang)
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except Exception:
                    pass
                send_welcome_with_video(bot, user_id, new_text, main_kbd)
            elif _is_webapp_mode(db) and config.APP_URL:
                webapp_url = (config.APP_URL or "").rstrip("/")
                if webapp_url.startswith("https://"):
                    webapp_url = webapp_url + "/webapp"
                    try:
                        new_markup = types.InlineKeyboardMarkup()
                        new_markup.add(types.InlineKeyboardButton(
                            get_text("menu_mode_webapp", lang),
                            web_app=types.WebAppInfo(url=webapp_url)
                        ))
                        try:
                            bot.delete_message(user_id, call.message.message_id)
                        except Exception:
                            pass
                        send_welcome_with_video(bot, user_id, new_text, new_markup)
                        _remove_reply_keyboard_silently(bot, user_id)
                    except Exception as e:
                        logger.warning("WebApp-Button (nav_main) fehlgeschlagen, Fallback: %s", e)
                        new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                        try:
                            bot.delete_message(user_id, call.message.message_id)
                        except Exception:
                            pass
                        send_welcome_with_video(bot, user_id, new_text, new_markup)
                        _remove_reply_keyboard_silently(bot, user_id)
                else:
                    new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                    try:
                        bot.delete_message(user_id, call.message.message_id)
                    except Exception:
                        pass
                    send_welcome_with_video(bot, user_id, new_text, new_markup)
                    _remove_reply_keyboard_silently(bot, user_id)
            else:
                new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except Exception:
                    pass
                send_welcome_with_video(bot, user_id, new_text, new_markup)
                _remove_reply_keyboard_silently(bot, user_id)
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            return

        elif target == "settings":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=settings"
                new_text = get_text("webapp_open_settings", lang)
                new_markup = types.InlineKeyboardMarkup()
                new_markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            else:
                settings = db.get_user_settings(user_id)
                new_text = get_text("settings_title", lang)
                new_markup = keyboards.get_settings_menu(settings, lang)

        elif target == "lang":
            new_text = "🌐 <b>Select Language / Sprache wählen:</b>"
            new_markup = keyboards.get_language_menu(lang)
            
        elif target == "profile":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=profile"
                new_text = get_text("webapp_open_profile", lang)
                new_markup = types.InlineKeyboardMarkup()
                new_markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            else:
                creds = db.get_user_credits(user_id)
                new_text = get_text("profile_text", lang).format(
                    name=call.from_user.first_name,
                    creds=creds,
                    user_id=user_id
                )
                new_markup = keyboards.get_back_menu(lang, target="nav_main")

        elif target == "referral":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=profile"
                new_text = get_text("webapp_open_profile", lang)
                new_markup = types.InlineKeyboardMarkup()
                new_markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            else:
                bot_name = bot.get_me().username
                link = f"https://t.me/{bot_name}?start={user_id}"
                new_text = get_text("share_menu_title", lang).format(ref_link=link)
                share_text = get_text("share_text_template", lang).format(ref_link=link)
                new_markup = keyboards.get_share_menu(link, share_text, lang)

        elif target == "support":
             new_text = get_text("support_text", lang)
             new_markup = keyboards.get_back_menu(lang, target="nav_main")

        if new_text and new_markup:
            try:
                bot.edit_message_text(
                    new_text, user_id, call.message.message_id,
                    reply_markup=new_markup, parse_mode="HTML",
                )
            except Exception:
                bot.send_message(user_id, new_text, reply_markup=new_markup, parse_mode="HTML")

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

    # 3. SETTINGS ACTIONS
    @bot.callback_query_handler(func=lambda c: c.data == "toggle_opt")
    def handle_toggle_opt(call):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings["auto_opt"] else 1
        db.update_setting(user_id, "auto_opt", new_val)
        
        new_settings = db.get_user_settings(user_id)
        lang = new_settings["lang"]
        bot.edit_message_reply_markup(
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(new_settings, lang),
        )
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data == "toggle_daily")
    def handle_toggle_daily(call):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings["daily_msg"] else 1
        db.update_setting(user_id, "daily_msg", new_val)
        
        new_settings = db.get_user_settings(user_id)
        lang = new_settings["lang"]
        bot.edit_message_reply_markup(
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(new_settings, lang),
        )
        status_key = "daily_news_on" if new_val else "daily_news_off"
        try:
            bot.answer_callback_query(call.id, get_text(status_key, lang))
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_lang_"))
    def handle_set_lang(call):
        user_id = call.message.chat.id
        new_lang = call.data.split("_")[2] 
        db.update_setting(user_id, "language", new_lang)
        
        settings = db.get_user_settings(user_id)
        
        try:
            bot.answer_callback_query(call.id, get_text("lang_selected", new_lang))
        except Exception:
            pass

        bot.edit_message_text(
            get_text("settings_title", new_lang),
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(settings, new_lang),
            parse_mode="HTML",
        )

    @bot.message_handler(commands=["cheat_mode"])
    def cheat(m):
        try:
            admin_id = int(os.getenv("ADMIN_ID", "0"))
        except (ValueError, TypeError):
            admin_id = 0
        if m.from_user.id == admin_id:
            db.update_credits(m.chat.id, 10000)
            lang = get_lang(m.chat.id)
            bot.reply_to(m, get_text("admin_cheat_success", lang))