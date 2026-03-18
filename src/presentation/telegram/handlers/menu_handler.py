import logging
import os

from telebot import TeleBot

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import clear_context, get_context
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

REFERRAL_REWARD = 50


def register(bot: TeleBot, generation_service, db) -> None:
    def get_lang(user_id):
        return db.get_user_settings(user_id)["lang"]

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
        
        # Modelle laden & Menü bauen
        all_models = db.get_all_models()
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