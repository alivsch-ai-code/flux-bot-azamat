"""
group_handler.py – Gruppen-spezifische Handler (aiogram 3).
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.config.settings import config
from src.presentation.telegram.handlers.chat_debounce import schedule_batched_text_message
from src.presentation.telegram.handlers.gen.chat_sessions import (
    append_global_chat_event,
    append_with_summary_if_needed,
    build_chat_prompt_from_messages,
)
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.presentation.telegram.runtime import get_telegram_loop
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

GEMINI_GROUP_MODEL = config.GEMINI_GROUP_MODEL


def get_group_menu_markup(db, chat_id: int, user_name: str = "") -> tuple:
    db.add_group_if_not_exists(chat_id, db.get_group_language(chat_id))
    lang = db.get_group_language(chat_id)
    name = (user_name or "").strip() or "there"
    text = get_text("grp_welcome", lang).format(name=name)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("grp_btn_credits", lang), callback_data="grp_shop")],
            [InlineKeyboardButton(text=get_text("grp_btn_lang", lang), callback_data="grp_lang_menu")],
            [InlineKeyboardButton(text=get_text("grp_btn_clear_history", lang), callback_data="grp_clear_history")],
        ]
    )
    return text, markup


async def _try_send_one_time_greeting(facade, db, generation_service, user_id: int, user_name: str, lang: str) -> None:
    if db.has_group_greeting_been_sent(user_id) or db.has_group_greeting_been_attempted(user_id):
        return
    db.mark_group_greeting_attempted(user_id)
    model = db.get_model_by_key(GEMINI_GROUP_MODEL)
    if not model or "text" not in (model.type or []):
        return
    prompt_template = get_text("grp_greeting_prompt", lang)
    prompt = f"{prompt_template}\n\nName: {user_name or 'User'}\n\nOutput ONLY the greeting text, nothing else."

    def _gen():
        return generation_service.process_request(user_id, model, prompt, media_files=None, no_charge=True, lang=lang)

    success, result = await asyncio.to_thread(_gen)
    if not success or not result:
        return
    try:
        await facade.send_message(user_id, str(result), parse_mode="HTML")
        append_global_chat_event(db, user_id, "assistant", str(result))
        db.mark_group_greeting_sent(user_id)
    except Exception as e:
        logger.debug("Could not send group greeting DM to %s: %s", user_id, e)


def register(router, facade, generation_service, db) -> None:
    def get_group_lang(chat_id: int) -> str:
        return db.get_group_language(chat_id)

    async def flush_group_batch_async(chat_id: int, batch: list) -> None:
        if not batch:
            return
        last_uid, last_name, last_text = batch[-1]
        model = db.get_model_by_key(GEMINI_GROUP_MODEL)
        if not model or "text" not in (model.type or []):
            try:
                await facade.send_message(chat_id, "⚠️ Gemini nicht verfügbar.", parse_mode="HTML")
            except Exception:
                pass
            return

        session_id = -abs(chat_id)
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

        def _gen():
            return generation_service.process_request(
                last_uid, model, full_prompt, media_files=None, group_chat_id=chat_id, lang=lang
            )

        success, result = await asyncio.to_thread(_gen)
        if not success:
            try:
                await facade.send_message(chat_id, str(result), parse_mode="HTML")
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
            await facade.send_message(chat_id, str(result), parse_mode="HTML")
        except Exception as e:
            logger.warning("Group batch reply send failed: %s", e)

    def flush_group_batch(chat_id: int, batch: list) -> None:
        # Kein fut.result() — sonst Deadlock, wenn der Debounce-Flush vom Event-Loop-Thread
        # (sofort bei ≥5 Nachrichten) aufgerufen wird: Loop kann die Coroutine nicht ausführen.
        loop = get_telegram_loop()

        async def _run() -> None:
            try:
                await flush_group_batch_async(chat_id, batch)
            except Exception:
                logger.exception("Group batch flush failed chat_id=%s", chat_id)

        asyncio.run_coroutine_threadsafe(_run(), loop)

    @router.message(Command("start"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_start(msg: Message):
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        db.add_group_if_not_exists(chat_id, db.get_group_language(chat_id))
        await _try_send_one_time_greeting(
            facade, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, get_group_lang(chat_id)
        )
        lang = get_group_lang(chat_id)
        name = msg.from_user.first_name or msg.from_user.username or "there"
        text = get_text("grp_welcome", lang).format(name=name)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("grp_btn_credits", lang), callback_data="grp_shop")],
                [InlineKeyboardButton(text=get_text("grp_btn_lang", lang), callback_data="grp_lang_menu")],
                [InlineKeyboardButton(text=get_text("grp_btn_clear_history", lang), callback_data="grp_clear_history")],
            ]
        )
        await facade.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    @router.message(Command("shop", "buy"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_shop(msg: Message):
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        await _try_send_one_time_greeting(
            facade, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, lang
        )
        try:
            await facade.send_message(chat_id, get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            await show_shop_logic(facade, fake_msg, db, lang, force_inline=True, group_chat_id=chat_id)
        except Exception as e:
            logger.warning("Group shop DM failed: %s", e)
            await facade.send_message(chat_id, get_text("grp_credits_start_first", lang), parse_mode="HTML")

    @router.message(F.text, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_text(msg: Message):
        if not msg.text or not msg.text.strip():
            return
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        db.add_user_if_not_exists(user_id, msg.from_user.username)
        lang = get_group_lang(chat_id)
        await _try_send_one_time_greeting(
            facade, db, generation_service, user_id, msg.from_user.first_name or msg.from_user.username, lang
        )

        model = db.get_model_by_key(GEMINI_GROUP_MODEL)
        if not model or "text" not in (model.type or []):
            await facade.send_message(chat_id, "⚠️ Gemini nicht verfügbar.", parse_mode="HTML")
            return

        user_name = msg.from_user.first_name or msg.from_user.username or "User"
        try:
            append_global_chat_event(db, user_id, "user", msg.text.strip(), user_name=user_name)
        except Exception:
            pass
        item = (user_id, user_name, msg.text.strip())
        schedule_batched_text_message(chat_id, item, flush_group_batch)

    @router.callback_query(F.data == "grp_shop", F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_cb_shop(call: CallbackQuery):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        db.add_group_if_not_exists(chat_id, get_group_lang(chat_id))
        lang = get_group_lang(chat_id)
        db.add_user_if_not_exists(user_id, call.from_user.username)
        await _try_send_one_time_greeting(
            facade, db, generation_service, user_id, call.from_user.first_name or call.from_user.username, lang
        )
        try:
            await call.answer(get_text("grp_credits_sent", lang))
            fake_msg = type("Msg", (), {"chat": type("C", (), {"id": user_id})(), "message_id": None})()
            await show_shop_logic(facade, fake_msg, db, lang, force_inline=True, group_chat_id=chat_id)
        except Exception as e:
            logger.warning("Group shop DM failed: %s", e)
            await call.answer(get_text("grp_credits_start_first", lang))

    @router.callback_query(F.data == "grp_lang_menu", F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_cb_lang_menu(call: CallbackQuery):
        chat_id = call.message.chat.id
        lang = get_group_lang(chat_id)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="grp_lang_de"),
                    InlineKeyboardButton(text="🇬🇧 English", callback_data="grp_lang_en"),
                ],
                [
                    InlineKeyboardButton(text="🇷🇺 Русский", callback_data="grp_lang_ru"),
                    InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="grp_lang_kk"),
                ],
            ]
        )
        try:
            await facade.edit_message_text(
                get_text("grp_btn_lang", lang) + ":", chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
            )
        except Exception:
            await facade.send_message(chat_id, get_text("grp_btn_lang", lang) + ":", reply_markup=markup, parse_mode="HTML")
        await call.answer()

    @router.callback_query(
        F.data.startswith("grp_lang_") & (F.data != "grp_lang_menu"),
        F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    )
    async def group_cb_set_lang(call: CallbackQuery):
        chat_id = call.message.chat.id
        new_lang = call.data.replace("grp_lang_", "")
        if new_lang in ("de", "en", "ru", "kk"):
            db.set_group_language(chat_id, new_lang)
            await call.answer(get_text("grp_lang_changed", new_lang))
            name = call.from_user.first_name or call.from_user.username or "there"
            text = get_text("grp_welcome", new_lang).format(name=name)
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("grp_btn_credits", new_lang), callback_data="grp_shop")],
                    [InlineKeyboardButton(text=get_text("grp_btn_lang", new_lang), callback_data="grp_lang_menu")],
                    [InlineKeyboardButton(text=get_text("grp_btn_clear_history", new_lang), callback_data="grp_clear_history")],
                ]
            )
            try:
                await facade.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                await facade.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data == "grp_clear_history", F.message.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def group_cb_clear_history(call: CallbackQuery):
        chat_id = call.message.chat.id
        lang = get_group_lang(chat_id)
        session_id = -abs(chat_id)
        model_key = f"{GEMINI_GROUP_MODEL}_group"
        try:
            db.clear_chat_session(session_id, model_key=model_key)
            await call.answer(get_text("history_cleared", lang))
        except Exception:
            await call.answer()
