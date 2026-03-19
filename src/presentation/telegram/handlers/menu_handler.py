import json
import logging
import os

from telebot import TeleBot, types

from src.config.settings import config
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import clear_context, get_context, set_context
from src.presentation.telegram.handlers.gen.nav_handlers import send_model_detail_view
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.utils.strings import get_text

logger = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

REFERRAL_REWARD = 50


def _is_keyboard_mode(db) -> bool:
    return db.get_bot_setting("menu_mode", "commands") == "keyboard"


def _is_webapp_mode(db) -> bool:
    return db.get_bot_setting("menu_mode", "commands") == "webapp"


def process_webapp_action(bot: TeleBot, user_id: int, action: str, db) -> None:
    """Führt eine Web-App-Aktion aus. Nutzbar von web_app_data-Handler und API."""
    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]
    lang = get_lang(user_id)
    all_models = db.get_all_models()
    clear_context(user_id)
    db.set_user_chat_mode(user_id, None, active=False)
    if action == "nav_main":
        welcome_text = get_text("welcome", lang)
        markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
        bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="HTML")
    elif action.startswith("nav_path_"):
        target_path = action.replace("nav_path_", "")
        markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)
        title_key = f"title_{target_path.replace('/', '_')}"
        title_text = get_text(title_key, lang)
        if title_text == title_key:
            cat_name = target_path.split("/")[-1].capitalize()
            display_name = get_text(f"menu_{cat_name.lower()}", lang)
            title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
        bot.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")
    elif action.startswith("sel_"):
        model_key = action.replace("sel_", "")
        send_model_detail_view(bot, user_id, model_key, db, get_lang)
    elif action == "cmd_shop":
        fake = type('Msg', (), {'chat': type('C', (), {'id': user_id})()})()
        show_shop_logic(bot, fake, db, lang)


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
                    welcome_text = get_text("welcome", lang)
                    markup = keyboards.get_main_reply_keyboard(lang)
                    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')
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
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    send_model_detail_view(bot, user_id, target, db, get_lang)
                    set_context(user_id, {"keyboard_path": path})
            return

        clear_context(user_id)
        db.set_user_chat_mode(user_id, None, active=False)
        if action == "nav_main":
            welcome_text = get_text("welcome", lang)
            markup = keyboards.get_main_reply_keyboard(lang)
            bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')
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
        lang = get_lang(user_id)
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
        try:
            bot.delete_message(user_id, message.message_id)
        except Exception:
            pass
        process_webapp_action(bot, user_id, action, db)

    # 1. START COMMAND
    @bot.message_handler(commands=['start'])
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


        welcome_text = get_text("welcome", lang)
        all_models = db.get_all_models()

        if _is_keyboard_mode(db):
            reply_kbd = keyboards.get_main_reply_keyboard(lang)
            bot.send_message(user_id, welcome_text, reply_markup=reply_kbd, parse_mode='HTML')
            grid_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            bot.send_message(user_id, "👇 <i>Tastatur aktiv – Kategorien auch unten am Eingabefeld</i>",
                            reply_markup=grid_markup, parse_mode='HTML')
        elif _is_webapp_mode(db) and config.APP_URL:
            webapp_url = config.APP_URL.rstrip("/") + "/webapp"
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton(
                get_text("menu_mode_webapp", lang),
                web_app=types.WebAppInfo(url=webapp_url)
            ))
            cat_btns = []
            for cat in ("image", "video", "audio", "text", "tools"):
                lbl = get_text(f"menu_{cat}", lang)
                if lbl.startswith("menu_"):
                    lbl = cat.capitalize()
                cat_btns.append(types.InlineKeyboardButton(lbl, callback_data=f"nav_path_{cat}"))
            markup.add(*cat_btns)
            markup.add(
                types.InlineKeyboardButton(get_text("menu_profile", lang), callback_data="nav_profile"),
                types.InlineKeyboardButton(get_text("menu_shop", lang), callback_data="cmd_shop"),
            )
            bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

    # 2. NAVIGATION (Static Menus)
    # WICHTIG: Wir ignorieren hier 'nav_path_', damit gen_handler diese übernehmen kann!
    @bot.callback_query_handler(func=lambda call: call.data.startswith('nav_') and not call.data.startswith('nav_path_'))
    def handle_navigation(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        
        try:
            target = call.data.split('_')[1]
        except IndexError:
            return # Falls Format falsch ist
        
        new_text = ""
        new_markup = None
        
        if target == "main":
            new_text = get_text("welcome", lang)
            all_models = db.get_all_models()
            new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            clear_context(user_id)
            if _is_keyboard_mode(db):
                main_kbd = keyboards.get_main_reply_keyboard(lang)
                bot.send_message(user_id, "👇", reply_markup=main_kbd, parse_mode="HTML")
            
        elif target == "settings":
            settings = db.get_user_settings(user_id)
            new_text = get_text("settings_title", lang)
            new_markup = keyboards.get_settings_menu(settings, lang)

        elif target == "lang":
            new_text = "🌐 <b>Select Language / Sprache wählen:</b>"
            new_markup = keyboards.get_language_menu(lang)
            
        elif target == "profile":
            creds = db.get_user_credits(user_id)
            new_text = get_text("profile_text", lang).format(
                name=call.from_user.first_name,
                creds=creds,
                user_id=user_id
            )
            new_markup = keyboards.get_back_menu(lang, target="nav_main") 

        elif target == "referral":
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