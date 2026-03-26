"""
group_handler.py – Gruppen-spezifische Handler

Nur für Gruppen: AZAMAT chatten mit Gemini, Credits kaufen, Sprache wechseln.
Private Chats werden von menu_handler und gen_handler verarbeitet.
"""

import logging

from telebot import TeleBot, types

from src.config.settings import config
from src.presentation.telegram.handlers.chat_debounce import schedule_batched_text_message
from src.presentation.telegram.handlers.gen.chat_sessions import (
    append_global_chat_event,
    append_with_summary_if_needed,
    build_chat_prompt_from_messages,
)
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

GEMINI_GROUP_MODEL = config.GEMINI_GROUP_MODEL


def _is_group(msg_or_call) -> bool:
    """Prüft ob die Nachricht/Callback aus einer Gruppe kommt. CallbackQuery hat .message.chat, Message hat .chat."""
    chat = msg_or_call.message.chat if hasattr(msg_or_call, "message") else msg_or_call.chat
    return str(chat.type) in ("group", "supergroup")


def get_group_menu_markup(db, chat_id: int, user_name: str = "") -> tuple:
    """Liefert (text, markup) für das Gruppenmenü – nur Credits + Sprache. Für private Chats nicht nutzen."""
    db.add_group_if_not_exists(chat_id, db.get_group_language(chat_id))
    lang = db.get_group_language(chat_id)
    name = (user_name or "").strip() or "there"
    text = get_text("grp_welcome", lang).format(name=name)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(get_text("grp_btn_credits", lang), callback_data="grp_shop"))
    markup.add(types.InlineKeyboardButton(get_text("grp_btn_lang", lang), callback_data="grp_lang_menu"))
    return text, markup


def _try_send_one_time_greeting(bot: TeleBot, db, generation_service, user_id: int, user_name: str, lang: str) -> None:
    """Sendet einmalig eine von Gemini generierte Willkommens-DM. Wird in DB vermerkt."""
    # Schutz: Wir senden die DM nicht jedes Mal neu.
    # In der DB wird sowohl "attempted" (versucht) als auch "sent" (tatsächlich zugestellt) vermerkt.
    # Dadurch verhindern wir Spam bei Retries/Deploy/Inkonsistenzen.
    if db.has_group_greeting_been_sent(user_id) or db.has_group_greeting_been_attempted(user_id):
        return
    db.mark_group_greeting_attempted(user_id)
    model = db.get_model_by_key(GEMINI_GROUP_MODEL)
    if not model or "text" not in (model.type or []):
        return
    prompt_template = get_text("grp_greeting_prompt", lang)
    prompt = f"{prompt_template}\n\nName: {user_name or 'User'}\n\nOutput ONLY the greeting text, nothing else."
    success, result = generation_service.process_request(user_id, model, prompt, media_files=None, no_charge=True)
    if not success or not result:
        return
    try:
        bot.send_message(user_id, str(result), parse_mode="HTML")
        append_global_chat_event(db, user_id, "assistant", str(result))
        db.mark_group_greeting_sent(user_id)
    except Exception as e:
        logger.debug("Could not send group greeting DM to %s: %s", user_id, e)


def register(bot: TeleBot, generation_service, db) -> None:
    """Registriert Gruppen-Handler. Muss VOR menu_handler und gen_handler registriert werden."""

    def get_group_lang(chat_id: int) -> str:
        return db.get_group_language(chat_id)

    def flush_group_batch(chat_id: int, batch: list) -> None:
        """Nach Debounce: alle gesammelten User-Nachrichten an Gemini, eine Antwort in die Gruppe."""
        if not batch:
            return
        last_uid, last_name, last_text = batch[-1]
        model = db.get_model_by_key(GEMINI_GROUP_MODEL)
        if not model or "text" not in (model.type or []):
            try:
                bot.send_message(chat_id, "⚠️ Gemini nicht verfügbar.", parse_mode="HTML")
            except Exception:
                pass
            return

        # Session-Key Mapping:
        # - Gruppenchat wird unter einem negativen session_id geführt,
        #   damit es sich von privaten User-IDs unterscheidet.
        session_id = -abs(chat_id)
        # - Chat History pro Modell-Key: wir erweitern den Gemini-Modell-Key um `_group`,
        #   damit Gruppen- und Privat-History nicht kollidieren.
        model_key = f"{GEMINI_GROUP_MODEL}_group"
        lang = get_group_lang(chat_id)
        system_prompt = get_text("azamat_system_prompt", lang)

        try:
            messages = None
            for _uid, user_name, piece in batch:
                messages = append_with_summary_if_needed(
                    db,
                    session_id,
                    model_key,
                    {"role": "user", "content": piece, "user_name": user_name},
                    max_messages=20,
                    summarize_at=20,
                )
            full_prompt = build_chat_prompt_from_messages(
                messages,
                last_text,
                system_prompt=system_prompt,
                current_user_name=last_name,
            )
        except Exception:
            block = "\n".join(f"{n}: {t}" for _u, n, t in batch)
            full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[HISTORY]\n{block}\nAssistant:"

        success, result = generation_service.process_request(
            last_uid, model, full_prompt, media_files=None, group_chat_id=chat_id
        )
        if not success:
            try:
                bot.send_message(chat_id, str(result), parse_mode="HTML")
            except Exception:
                pass
            return
        try:
            append_with_summary_if_needed(
                db,
                session_id,
                model_key,
                {"role": "assistant", "content": str(result)},
                max_messages=20,
                summarize_at=20,
            )
            append_global_chat_event(db, last_uid, "assistant", str(result))
        except Exception:
            pass
        try:
            bot.send_message(chat_id, str(result), parse_mode="HTML")
        except Exception as e:
            logger.warning("Group batch reply send failed: %s", e)

    # --- /start in Gruppe ---
    @bot.message_handler(commands=["start"], func=lambda m: _is_group(m))
    def group_start(msg):
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        db.add_group_if_not_exists(chat_id, db.get_group_language(chat_id))
        _try_send_one_time_greeting(bot, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, get_group_lang(chat_id))
        lang = get_group_lang(chat_id)
        name = msg.from_user.first_name or msg.from_user.username or "there"
        text = get_text("grp_welcome", lang).format(name=name)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(get_text("grp_btn_credits", lang), callback_data="grp_shop"))
        markup.add(types.InlineKeyboardButton(get_text("grp_btn_lang", lang), callback_data="grp_lang_menu"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    # --- /shop in Gruppe ---
    @bot.message_handler(commands=["shop", "buy"], func=lambda m: _is_group(m))
    def group_shop(msg):
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        _try_send_one_time_greeting(bot, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, lang)
        try:
            bot.send_message(chat_id, get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            show_shop_logic(bot, fake_msg, db, lang, force_inline=True, group_chat_id=chat_id)
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
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        lang = get_group_lang(chat_id)
        _try_send_one_time_greeting(bot, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, lang)

        model = db.get_model_by_key(GEMINI_GROUP_MODEL)
        if not model or "text" not in (model.type or []):
            bot.send_message(chat_id, "⚠️ Gemini nicht verfügbar.", parse_mode="HTML")
            return

        user_name = msg.from_user.first_name or msg.from_user.username or "User"
        try:
            append_global_chat_event(db, user_id, "user", msg.text.strip(), user_name=user_name)
        except Exception:
            pass
        item = (user_id, user_name, msg.text.strip())
        schedule_batched_text_message(chat_id, item, flush_group_batch)

    # --- Callback: Credits in Gruppe → Shop per DM ---
    @bot.callback_query_handler(func=lambda c: c.data == "grp_shop" and _is_group(c))
    def group_cb_shop(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, call.from_user.username)
        _try_send_one_time_greeting(bot, db, generation_service, user_id, call.from_user.first_name or call.from_user.username, lang)
        try:
            bot.answer_callback_query(call.id, get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            show_shop_logic(bot, fake_msg, db, lang, force_inline=True, group_chat_id=chat_id)
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
            # Zurück zum Willkommen (ohne Namen bei Sprachwechsel – "there"/"du" etc.)
            name = call.from_user.first_name or call.from_user.username or "there"
            text = get_text("grp_welcome", new_lang).format(name=name)
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(get_text("grp_btn_credits", new_lang), callback_data="grp_shop"))
            markup.add(types.InlineKeyboardButton(get_text("grp_btn_lang", new_lang), callback_data="grp_lang_menu"))
            try:
                bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
