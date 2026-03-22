"""
group_handler.py – Gruppen-spezifische Handler

Nur für Gruppen: AZAMAT chatten mit Gemini, Credits kaufen, Sprache wechseln.
Private Chats werden von menu_handler und gen_handler verarbeitet.
"""

import logging

from telebot import TeleBot, types

from src.presentation.telegram.handlers.gen.chat_sessions import append_with_summary_if_needed, build_chat_prompt_from_messages
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

GEMINI_GROUP_MODEL = "google-gemini-2-5-flash"


def _is_group(msg_or_call) -> bool:
    """Prüft ob die Nachricht/Callback aus einer Gruppe kommt."""
    chat = msg_or_call.chat
    return str(chat.type) in ("group", "supergroup")


def register(bot: TeleBot, generation_service, db) -> None:
    """Registriert Gruppen-Handler. Muss VOR menu_handler und gen_handler registriert werden."""

    def get_group_lang(chat_id: int) -> str:
        return db.get_group_language(chat_id)

    # --- /start in Gruppe ---
    @bot.message_handler(commands=["start"], func=lambda m: _is_group(m))
    def group_start(msg):
        chat_id = msg.chat.id
        lang = get_group_lang(chat_id)
        text = get_text("grp_welcome", lang)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(get_text("grp_btn_credits", lang), callback_data="grp_shop"))
        markup.add(types.InlineKeyboardButton(get_text("grp_btn_lang", lang), callback_data="grp_lang_menu"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    # --- /shop in Gruppe ---
    @bot.message_handler(commands=["shop", "buy"], func=lambda m: _is_group(m))
    def group_shop(msg):
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        try:
            bot.send_message(chat_id, get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            show_shop_logic(bot, fake_msg, db, lang)
        except Exception as e:
            logger.warning("Group shop DM failed: %s", e)
            bot.send_message(chat_id, get_text("grp_credits_start_first", lang), parse_mode="HTML")

    # --- Text in Gruppe → Gemini mit AZAMAT-Rolle ---
    @bot.message_handler(content_types=["text"], func=lambda m: _is_group(m))
    def group_text(msg):
        if not msg.text or not msg.text.strip():
            return
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        lang = get_group_lang(chat_id)

        model = db.get_model_by_key(GEMINI_GROUP_MODEL)
        if not model or "text" not in (model.type or []):
            bot.send_message(chat_id, "⚠️ Gemini nicht verfügbar.", parse_mode="HTML")
            return

        # Session pro Gruppe (chat_id als user_id-Ersatz)
        session_id = -abs(chat_id)
        model_key = f"{GEMINI_GROUP_MODEL}_group"
        system_prompt = get_text("azamat_system_prompt", lang)

        try:
            messages = append_with_summary_if_needed(db, session_id, model_key, {"role": "user", "content": msg.text})
            full_prompt = build_chat_prompt_from_messages(messages, msg.text, system_prompt=system_prompt)
        except Exception:
            full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[HISTORY]\nUser: {msg.text}\nAssistant:"

        success, result = generation_service.process_request(user_id, model, full_prompt, media_files=None)
        if not success:
            bot.send_message(chat_id, str(result), parse_mode="HTML")
            return
        # Assistant-Antwort in Session speichern für Kontext
        try:
            append_with_summary_if_needed(db, session_id, model_key, {"role": "assistant", "content": str(result)})
        except Exception:
            pass
        bot.send_message(chat_id, str(result), parse_mode="HTML")

    # --- Callback: Credits in Gruppe → Shop per DM ---
    @bot.callback_query_handler(func=lambda c: c.data == "grp_shop" and _is_group(c))
    def group_cb_shop(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, call.from_user.username)
        try:
            bot.answer_callback_query(call.id, get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            show_shop_logic(bot, fake_msg, db, lang)
        except Exception as e:
            logger.warning("Group shop DM failed: %s", e)
            bot.answer_callback_query(call.id, get_text("grp_credits_start_first", lang))

    # --- Callback: Sprachmenü ---
    @bot.callback_query_handler(func=lambda c: c.data == "grp_lang_menu" and _is_group(c))
    def group_cb_lang_menu(call):
        chat_id = call.message.chat.id
        lang = get_group_lang(chat_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🇩🇪 Deutsch", callback_data="grp_lang_de"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="grp_lang_en"),
        )
        markup.add(
            types.InlineKeyboardButton("🇷🇺 Русский", callback_data="grp_lang_ru"),
            types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="grp_lang_kk"),
        )
        try:
            bot.edit_message_text(get_text("grp_btn_lang", lang) + ":", chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, get_text("grp_btn_lang", lang) + ":", reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)

    # --- Callback: Sprache setzen ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("grp_lang_") and c.data != "grp_lang_menu" and _is_group(c))
    def group_cb_set_lang(call):
        chat_id = call.message.chat.id
        new_lang = call.data.replace("grp_lang_", "")
        if new_lang in ("de", "en", "ru", "kk"):
            db.set_group_language(chat_id, new_lang)
            bot.answer_callback_query(call.id, get_text("grp_lang_changed", new_lang))
            # Zurück zum Willkommen
            text = get_text("grp_welcome", new_lang)
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(get_text("grp_btn_credits", new_lang), callback_data="grp_shop"))
            markup.add(types.InlineKeyboardButton(get_text("grp_btn_lang", new_lang), callback_data="grp_lang_menu"))
            try:
                bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
