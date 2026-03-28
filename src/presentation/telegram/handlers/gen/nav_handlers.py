"""
nav_handlers.py – Navigation und Modell-Auswahl (aiogram 3).
"""

from __future__ import annotations

import logging
import time
from urllib.parse import quote

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.config.settings import config
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.chat_debounce import cancel_pending_batch
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.group_handler import get_group_menu_markup
from src.presentation.telegram.welcome_utils import send_welcome_with_video
from src.utils.strings import get_text, get_welcome

logger = logging.getLogger(__name__)


async def send_model_detail_view(facade, user_id: int, model_key: str, db, get_lang) -> bool:
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
        await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return True

    text = f"{preview_link}🤖 <b>{model.name}</b>\n{model.description}{example_block}\n\n💰 <b>Kosten: {final_cost} Credits</b>"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🚀 Start ({final_cost} Credits)", callback_data=f"start_gen_{model_key}")],
            [keyboards.btn(get_text("btn_back", lang), f"nav_path_{model.menu_path}")],
        ]
    )
    await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
    return True


def register_nav_handlers(router, facade, db, get_lang) -> None:
    async def _show_group_menu_if_group(call: CallbackQuery) -> bool:
        chat_type = str(call.message.chat.type)
        if chat_type in ("group", "supergroup"):
            chat_id = call.message.chat.id
            name = (call.from_user.first_name or call.from_user.username or "") if call.from_user else ""
            text, markup = get_group_menu_markup(db, chat_id, name)
            try:
                await facade.edit_message_text(
                    text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                await facade.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            try:
                await call.answer()
            except Exception:
                pass
            return True
        return False

    @router.callback_query(F.data.startswith("nav_path_"))
    async def handle_path_nav(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
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
                await facade.delete_message(user_id, call.message.message_id)
            except Exception as e:
                logger.warning("Delete failed in handle_path_nav: %s", e)
            await facade.send_message(user_id, title_text, reply_markup=path_kbd, parse_mode="HTML")
        elif menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp?path=" + quote(target_path, safe="")
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=webapp_url))]
                ]
            )
            try:
                await facade.edit_message_text(
                    title_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
                )
            except Exception as e:
                logger.warning("Edit failed in handle_path_nav: %s", e)
                await facade.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)
            try:
                await facade.edit_message_text(
                    title_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
                )
            except Exception as e:
                logger.warning("Edit failed in handle_path_nav: %s", e)
                await facade.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data.startswith("sel_"))
    async def handle_model_click(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        key = call.data.split("sel_")[1]
        model = db.get_model_by_key(key)
        if not model or not model.is_active:
            await call.answer(get_text("err_model_maintenance", lang) or "⚠️ Inactive.", show_alert=False)
            return

        menu_mode = db.get_bot_setting("menu_mode", "commands")
        if menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp?model=" + quote(key, safe="")
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=webapp_url))]
                ]
            )
            text = get_text("webapp_open_model", lang).format(name=model.name)
            try:
                await facade.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            try:
                await call.answer()
            except Exception:
                pass
            return

        prev = get_context(user_id) or {}
        set_context(
            user_id,
            {
                "model_key": key,
                "step": "viewing_model",
                "menu_path": model.menu_path,
                "last_bot_msg_id": call.message.message_id,
                "media_paths": prev.get("media_paths") or [],
            },
        )
        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)

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
            base = get_text("ask_chat_mode", lang).format(cost=final_cost)
            text = f"{preview_link}{base}{example_block}"
            markup = keyboards.get_chat_mode_ask_menu(key, lang)
            await facade.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        text = f"{preview_link}🤖 <b>{model.name}</b>\n{model.description}{example_block}\n\n💰 <b>Kosten: {final_cost} Credits</b>"
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🚀 Start ({final_cost} Credits)", callback_data=f"start_gen_{key}")],
                [keyboards.btn(get_text("btn_back", lang), f"nav_path_{model.menu_path}")],
            ]
        )
        await facade.edit_message_text(
            text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False
        )

    @router.callback_query(F.data.startswith("chat_mode_"))
    async def handle_chat_decision(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        data = call.data
        if "chat_mode_yes_" in data:
            action, key = "yes", data.replace("chat_mode_yes_", "")
        else:
            action, key = "no", data.replace("chat_mode_no_", "")
        model = db.get_model_by_key(key)
        if not model:
            await call.answer("Model error")
            return
        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
        if action == "yes":
            db.set_user_chat_mode(user_id, key, active=True)
            text = get_text("chat_active_msg", lang).format(model=model.name, cost=final_cost)
            markup = keyboards.get_chat_active_menu(lang)
            await facade.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            db.set_user_chat_mode(user_id, None, active=False)
            cancel_pending_batch(user_id)
            set_context(
                user_id,
                {
                    "model_key": key,
                    "step": "waiting_for_prompt",
                    "last_bot_msg_id": call.message.message_id,
                    "menu_path": model.menu_path,
                },
            )
            prompt_text = get_text("model_req_prompt", lang)
            markup = keyboards.get_back_menu(lang, target=f"sel_{key}")
            await facade.edit_message_text(prompt_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        try:
            await call.answer()
        except Exception:
            pass

    @router.callback_query(F.data == "stop_chat")
    async def handle_stop_chat(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
        user_id = call.message.chat.id
        cancel_pending_batch(user_id)
        lang = get_lang(user_id)
        try:
            await call.answer()
        except Exception:
            pass
        text = (
            get_text("chat_ended", lang)
            + "\n\n"
            + "Möchtest du den bisherigen Chatverlauf löschen oder behalten?"
        )
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🧹 Verlauf löschen", callback_data="stop_chat_clear"),
                    InlineKeyboardButton(text="📚 Verlauf behalten", callback_data="stop_chat_keep"),
                ]
            ]
        )
        await facade.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data.in_(("reuse_media_yes", "reuse_media_no", "reuse_media_text")))
    async def handle_reuse_media_decision(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        ctx = get_context(user_id) or {}
        recent = list(ctx.get("recent_media_paths") or [])
        expires_at = int(ctx.get("recent_media_expires_at") or 0)
        last_prompt = str(ctx.get("last_prompt") or "").strip()
        model_key = str(ctx.get("model_key") or "").strip()
        is_valid = bool(recent) and int(time.time()) <= expires_at
        if call.data == "reuse_media_yes":
            if is_valid:
                ctx["media_paths"] = recent
                set_context(user_id, ctx)
                await call.answer(get_text("reuse_media_enabled", lang))
            else:
                ctx["media_paths"] = []
                ctx["recent_media_paths"] = []
                ctx["recent_media_expires_at"] = 0
                set_context(user_id, ctx)
                await call.answer(get_text("reuse_media_expired", lang))
        elif call.data == "reuse_media_no":
            ctx["media_paths"] = []
            if last_prompt:
                ctx["pending_webapp_prompt"] = last_prompt
            set_context(user_id, ctx)
            await call.answer(get_text("reuse_media_disabled", lang))
            if config.APP_URL and model_key:
                webapp_url = config.APP_URL.rstrip("/") + "/webapp?model=" + quote(model_key, safe="")
                if last_prompt:
                    webapp_url += "&prompt=" + quote(last_prompt, safe="")
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=webapp_url)
                            )
                        ]
                    ]
                )
                await facade.send_message(user_id, get_text("reuse_media_open_webapp", lang), reply_markup=markup, parse_mode="HTML")
        else:
            ctx["media_paths"] = []
            if last_prompt:
                ctx["pending_webapp_prompt"] = last_prompt
            set_context(user_id, ctx)
            await call.answer(get_text("btn_reuse_media_text", lang))
            model_name = model_key or "-"
            if model_key:
                model = db.get_model_by_key(model_key)
                if model and model.name:
                    model_name = model.name
            await facade.send_message(
                user_id,
                get_text("model_req_prompt_with_model", lang).format(model=model_name),
                reply_markup=keyboards.get_back_menu(lang, target=f"sel_{model_key}") if model_key else None,
                parse_mode="HTML",
            )
            if config.APP_URL and model_key:
                webapp_url = config.APP_URL.rstrip("/") + "/webapp?model=" + quote(model_key, safe="")
                if last_prompt:
                    webapp_url += "&prompt=" + quote(last_prompt, safe="")
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=webapp_url)
                            )
                        ]
                    ]
                )
                await facade.send_message(user_id, get_text("reuse_media_open_webapp", lang), reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data.in_(("stop_chat_clear", "stop_chat_keep")))
    async def handle_stop_chat_decision(call: CallbackQuery):
        if await _show_group_menu_if_group(call):
            return
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        action = call.data
        if action == "stop_chat_clear":
            try:
                db.clear_chat_session(user_id)
            except Exception:
                pass
        db.set_user_chat_mode(user_id, None, active=False)
        cancel_pending_batch(user_id)
        try:
            await call.answer()
        except Exception:
            pass
        from src.presentation.telegram.handlers.common import clear_context

        clear_context(user_id)
        all_models = db.get_all_models()
        user_name = db.get_user_username_or_name(user_id) or ""
        text = get_welcome(lang, user_name)
        menu_mode = db.get_bot_setting("menu_mode", "commands")
        try:
            await facade.delete_message(user_id, call.message.message_id)
        except Exception:
            pass
        if menu_mode == "keyboard":
            main_kbd = keyboards.get_main_reply_keyboard(lang)
            await send_welcome_with_video(facade, user_id, text, main_kbd)
        elif menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
            webapp_url = config.APP_URL.rstrip("/") + "/webapp"
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=webapp_url))]
                ]
            )
            await send_welcome_with_video(facade, user_id, text, markup)
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            await send_welcome_with_video(facade, user_id, text, markup)
