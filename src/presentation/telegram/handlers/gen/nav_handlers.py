"""
nav_handlers.py – Navigation und Modell-Auswahl

Registriert die Callback-Handler für:
- handle_path_nav: Navigation durch Kategorien (nav_path_*)
- handle_model_click: Modell anklicken (sel_*) → Detailansicht oder Chat-Modus-Abfrage
- handle_chat_decision: Chat Ja/Nein (chat_mode_yes_/chat_mode_no_) → Context setzen oder Chat aktivieren
- handle_stop_chat: Chat beenden (stop_chat) → Hauptmenü

Alle Handler nutzen keyboards.get_dynamic_model_menu, get_chat_mode_ask_menu usw.
"""

import logging

from urllib.parse import quote
from telebot import TeleBot, types

from src.config.settings import config
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import set_context
from src.utils.strings import get_text, get_welcome

logger = logging.getLogger(__name__)


def send_model_detail_view(bot: TeleBot, user_id: int, model_key: str, db, get_lang) -> bool:
    """Sendet Modell-Detailansicht (für Tastatur-Navigation). Returns True wenn erfolgreich."""
    model = db.get_model_by_key(model_key)
    if not model or not model.is_active:
        return False
    lang = get_lang(user_id)
    final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
    preview_link = ""
    example_block = ""
    if model.example_data and isinstance(model.example_data, dict):
        url = model.example_data.get("output_image") or model.example_data.get("image") or model.example_data.get("url")
        if url and str(url).startswith("http"):
            preview_link = f"<a href='{url}'>&#8205;</a>"
        ex_prompt = (model.example_data.get("prompt") or model.example_data.get("example_prompt") or "").strip()
        if ex_prompt:
            short = ex_prompt[:300] + "..." if len(ex_prompt) > 300 else ex_prompt
            example_block = f"\n\n📝 <b>Beispiel-Prompt:</b>\n<code>{short}</code>"
        elif url:
            example_block = "\n\n🖼️ <i>Dieses Modell hat ein Beispielbild oben in der Vorschau.</i>"

    if model.type and "text" in model.type:
        base = get_text("ask_chat_mode", lang).format(cost=final_cost)
        text = f"{preview_link}{base}{example_block}"
        markup = keyboards.get_chat_mode_ask_menu(model_key, lang)
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return True

    text = f"{preview_link}🤖 <b>{model.name}</b>\n{model.description}{example_block}\n\n💰 <b>Kosten: {final_cost} Credits</b>"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(f"🚀 Start ({final_cost} Credits)", callback_data=f"start_gen_{model_key}"))
    markup.add(types.InlineKeyboardButton(get_text("btn_back", lang), callback_data=f"nav_path_{model.menu_path}"))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
    return True


def register_nav_handlers(bot: TeleBot, db, get_lang) -> None:
    """Registriert alle Navigations- und Modell-Click-Handler."""

    @bot.callback_query_handler(func=lambda c: c.data.startswith('nav_path_'))
    def handle_path_nav(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        target_path = call.data.replace("nav_path_", "")
        all_models = db.get_all_models()
        menu_mode = db.get_bot_setting("menu_mode", "commands")
        title_key = f"title_{target_path.replace('/', '_')}"
        title_text = get_text(title_key, lang)
        if title_text == title_key:
            cat_name = target_path.split("/")[-1].capitalize()
            display_name = get_text(f"menu_{cat_name.lower()}", lang)
            if display_name.startswith("menu_"):
                display_name = cat_name
            title_text = f"📂 <b>{display_name}</b>"
        if menu_mode == "keyboard":
            set_context(user_id, {"keyboard_path": target_path})
            path_kbd = keyboards.get_path_reply_keyboard(all_models, lang, target_path)
            try:
                bot.delete_message(user_id, call.message.message_id)
            except Exception as e:
                logger.warning("Delete failed in handle_path_nav: %s", e)
            bot.send_message(user_id, title_text, reply_markup=path_kbd, parse_mode="HTML")
        elif menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp?path=" + quote(target_path, safe="")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            try:
                bot.edit_message_text(title_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                logger.warning("Edit failed in handle_path_nav: %s", e)
                bot.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)
            try:
                bot.edit_message_text(title_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                logger.warning("Edit failed in handle_path_nav: %s", e)
                bot.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_model_click(call):
        from src.presentation.telegram.handlers.common import get_context, set_context
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        key = call.data.split('sel_')[1]
        model = db.get_model_by_key(key)
        if not model or not model.is_active:
            bot.answer_callback_query(call.id, get_text("err_model_maintenance", lang) or "⚠️ Inactive.")
            return

        menu_mode = db.get_bot_setting("menu_mode", "commands")
        if menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp?model=" + quote(key, safe="")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            text = get_text("webapp_open_model", lang).format(name=model.name)
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            return

        prev = get_context(user_id) or {}
        set_context(user_id, {
            "model_key": key,
            "step": "viewing_model",
            "menu_path": model.menu_path,
            "last_bot_msg_id": call.message.message_id,
            "media_paths": prev.get("media_paths") or [],
        })
        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)

        # Beispielbild und Beispiel-Prompt immer vorbereiten (auch für Text-Modelle)
        preview_link = ""
        example_block = ""
        if model.example_data and isinstance(model.example_data, dict):
            url = model.example_data.get("output_image") or model.example_data.get("image") or model.example_data.get("url")
            if url and str(url).startswith("http"):
                preview_link = f"<a href='{url}'>&#8205;</a>"
            ex_prompt = (model.example_data.get("prompt") or model.example_data.get("example_prompt") or "").strip()
            if ex_prompt:
                short = ex_prompt
                if len(short) > 300:
                    short = short[:300] + "..."
                example_block = f"\n\n📝 <b>Beispiel-Prompt:</b>\n<code>{short}</code>"
            elif url:
                example_block = "\n\n🖼️ <i>Dieses Modell hat ein Beispielbild oben in der Vorschau.</i>"

        if model.type and "text" in model.type:
            # Chat-Mode-Abfrage mit optionalem Beispielbild/-prompt
            base = get_text("ask_chat_mode", lang).format(cost=final_cost)
            text = f"{preview_link}{base}{example_block}"
            markup = keyboards.get_chat_mode_ask_menu(key, lang)
            bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        text = f"{preview_link}🤖 <b>{model.name}</b>\n{model.description}{example_block}\n\n💰 <b>Kosten: {final_cost} Credits</b>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"🚀 Start ({final_cost} Credits)", callback_data=f"start_gen_{key}"))
        markup.add(types.InlineKeyboardButton(get_text("btn_back", lang), callback_data=f"nav_path_{model.menu_path}"))
        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('chat_mode_'))
    def handle_chat_decision(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        data = call.data
        if "chat_mode_yes_" in data:
            action, key = "yes", data.replace("chat_mode_yes_", "")
        else:
            action, key = "no", data.replace("chat_mode_no_", "")
        model = db.get_model_by_key(key)
        if not model:
            bot.answer_callback_query(call.id, "Model error")
            return
        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
        if action == "yes":
            db.set_user_chat_mode(user_id, key, active=True)
            text = get_text("chat_active_msg", lang).format(model=model.name, cost=final_cost)
            markup = keyboards.get_chat_active_menu(lang)
            bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            db.set_user_chat_mode(user_id, None, active=False)
            set_context(user_id, {"model_key": key, "step": "waiting_for_prompt", "last_bot_msg_id": call.message.message_id, "menu_path": model.menu_path})
            prompt_text = get_text("model_req_prompt", lang)
            markup = keyboards.get_back_menu(lang, target=f"sel_{key}")
            bot.edit_message_text(prompt_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data == 'stop_chat')
    def handle_stop_chat(call):
        """Fragt beim Beenden des Chats, ob der Verlauf gelöscht werden soll."""
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        text = (
            get_text("chat_ended", lang)
            + "\n\n"
            + "Möchtest du den bisherigen Chatverlauf löschen oder behalten?"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🧹 Verlauf löschen", callback_data="stop_chat_clear"),
            types.InlineKeyboardButton("📚 Verlauf behalten", callback_data="stop_chat_keep"),
        )
        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data in ("stop_chat_clear", "stop_chat_keep"))
    def handle_stop_chat_decision(call):
        """Verarbeitet die Entscheidung des Users zum Chatverlauf."""
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        action = call.data
        if action == "stop_chat_clear":
            try:
                db.clear_chat_session(user_id)
            except Exception:
                pass
        db.set_user_chat_mode(user_id, None, active=False)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        from src.presentation.telegram.handlers.common import clear_context
        clear_context(user_id)
        all_models = db.get_all_models()
        user_name = db.get_user_username_or_name(user_id) or ""
        text = get_welcome(lang, user_name)
        menu_mode = db.get_bot_setting("menu_mode", "commands")
        if menu_mode == "keyboard":
            main_kbd = keyboards.get_main_reply_keyboard(lang)
            try:
                bot.delete_message(user_id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(user_id, text, reply_markup=main_kbd, parse_mode="HTML")
        elif menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(get_text("menu_mode_webapp", lang), web_app=types.WebAppInfo(url=webapp_url)))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
