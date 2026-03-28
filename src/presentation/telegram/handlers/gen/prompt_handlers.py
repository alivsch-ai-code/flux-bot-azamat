"""
prompt_handlers.py – Text-Prompt (aiogram 3).
"""

from __future__ import annotations

import asyncio
import time

from aiogram import F
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.config.settings import config
from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_bundle_via_llm
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import clear_context, get_context, set_context
from src.presentation.telegram.handlers.gen import (
    cleanup_pending_prompts,
    ctx_media_to_list,
    path_to_mediafile,
    pending_prompts,
)
from src.presentation.telegram.handlers.gen.chat_sessions import (
    append_global_chat_event,
    append_with_summary_if_needed,
    build_chat_prompt_from_messages,
)
from src.utils.strings import get_text


def register_prompt_handlers(router, facade, db, get_lang, run_generation) -> None:
    def _model_supports_negative_prompt(model) -> bool:
        schema = getattr(model, "input_schema", None) or {}
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        for key in ("negative_prompt", "negative", "negative_text", "neg_prompt"):
            if key in properties:
                return True
        return False

    async def flush_private_chat_async(chat_id: int, batch: list) -> None:
        if not batch:
            return
        chat_state = None
        try:
            chat_state = db.get_user_chat_state(chat_id)
        except Exception:
            chat_state = None
        if not chat_state or not chat_state.get("is_chat") or not chat_state.get("model_key"):
            return

        model_key = chat_state["model_key"]
        model = db.get_model_by_key(model_key)
        is_text_model = bool(model and model.type and "text" in model.type)
        _, last_name, last_text = batch[-1]

        if not is_text_model:
            combined = "\n---\n".join(f"{name}: {t}" for _u, name, t in batch)
            await run_generation(chat_id, model_key, combined, media_files=None, is_chat=True)
            return

        try:
            messages = None
            for _uid, user_name, piece in batch:
                messages = append_with_summary_if_needed(
                    db,
                    chat_id,
                    model_key,
                    {"role": "user", "content": piece, "user_name": user_name},
                )
            lang = get_lang(chat_id)
            sys_prompt = get_text("azamat_private_chat_prompt", lang)
            sys_prompt = f"{sys_prompt}\n\n{get_text('azamat_user_name_hint', lang).format(name=last_name)}"
            full_prompt = build_chat_prompt_from_messages(
                messages,
                last_text,
                system_prompt=sys_prompt,
                current_user_name=last_name,
            )
            await run_generation(
                chat_id,
                model_key,
                full_prompt,
                media_files=None,
                is_chat=True,
                chat_history_mode="persistent",
                chat_user_name=last_name,
            )
        except Exception:
            combined = "\n\n".join(f"{name}: {t}" for _u, name, t in batch)
            await run_generation(
                chat_id,
                model_key,
                combined,
                media_files=None,
                is_chat=True,
                chat_history_mode="once_off",
                chat_user_name=last_name,
            )

    @router.message(F.text, F.chat.type == ChatType.PRIVATE)
    async def on_prompt(msg: Message):
        user_id = msg.chat.id
        text = (msg.text or "").strip()
        if not text or text.startswith("/"):
            return

        try:
            user_name = (msg.from_user and msg.from_user.first_name) or "User"
            append_global_chat_event(db, user_id, "user", text, user_name=user_name)
        except Exception:
            pass

        ctx = get_context(user_id)

        chat_state = None
        try:
            chat_state = db.get_user_chat_state(user_id)
        except Exception:
            chat_state = None

        if chat_state and chat_state.get("is_chat") and chat_state.get("model_key"):
            tg_uid = msg.from_user.id if msg.from_user else user_id
            user_name = (msg.from_user and msg.from_user.first_name) or "User"
            # Privatchat: ohne Debounce — sofort antworten (Gruppen nutzen weiter Batching in group_handler).
            await flush_private_chat_async(user_id, [(tg_uid, user_name, text)])
            return

        if ctx.get("step") == "awaiting_telegram_chat_choice":
            set_context(user_id, {**ctx, "pending_chat_prompt_text": text})
            return

        if not ctx:
            lang = get_lang(user_id)
            default_model_key = config.GEMINI_GROUP_MODEL
            model = db.get_model_by_key(default_model_key)
            if model and model.type and "text" in model.type:
                cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
                ask = get_text("ask_chat_mode", lang).format(cost=cost)
                set_context(
                    user_id,
                    {
                        "step": "awaiting_telegram_chat_choice",
                        "pending_chat_model_key": default_model_key,
                        "pending_chat_prompt_text": text,
                    },
                )
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            keyboards.btn(get_text("btn_yes_chat", lang), "tgchat_yes"),
                            keyboards.btn(get_text("btn_no_chat", lang), "tgchat_no"),
                        ]
                    ]
                )
                await facade.send_message(user_id, ask, reply_markup=markup, parse_mode="HTML")
            return

        if ctx.get("step") == "waiting_for_prompt":
            model = db.get_model_by_key(ctx["model_key"])
            is_text_model = bool(model and model.type and "text" in model.type)
            settings = db.get_user_settings(user_id)
            user_name = (msg.from_user and msg.from_user.first_name) or "User"
            if settings.get("auto_opt", True):
                msg_wait = await facade.send_message(user_id, get_text("optimizing_msg", get_lang(user_id)), parse_mode="HTML")
                try:
                    bundle = await asyncio.to_thread(optimize_prompt_bundle_via_llm, msg.text)
                    optimized = bundle.get("optimized_prompt") or msg.text
                    negative_prompt = bundle.get("negative_prompt")
                    if not settings.get("auto_negative_prompt", True):
                        negative_prompt = None
                    supports_negative = bool(model and _model_supports_negative_prompt(model))
                    if not supports_negative:
                        negative_prompt = None
                    pending_prompts[user_id] = {
                        "original": msg.text,
                        "optimized": optimized,
                        "negative_prompt": negative_prompt,
                        "model_key": ctx["model_key"],
                        "media_files": ctx.get("media_paths", []),
                        "timestamp": time.time(),
                    }
                    cleanup_pending_prompts()
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=get_text("btn_accept", get_lang(user_id)), callback_data="prompt_accept"
                                ),
                                InlineKeyboardButton(
                                    text=get_text("btn_reject", get_lang(user_id)), callback_data="prompt_reject"
                                ),
                            ]
                        ]
                    )
                    opt_text = get_text("opt_result_msg", get_lang(user_id)).format(
                        original=msg.text, optimized=optimized
                    )
                    if negative_prompt:
                        opt_text += f"\n\n<b>Negative Prompt:</b>\n<code>{negative_prompt}</code>"
                    await facade.edit_message_text(
                        opt_text, user_id, msg_wait.message_id, reply_markup=markup, parse_mode="HTML"
                    )
                except Exception:
                    await run_generation(
                        user_id,
                        ctx["model_key"],
                        msg.text,
                        ctx_media_to_list(ctx),
                        is_chat=False,
                        chat_history_mode="once_off" if is_text_model else None,
                        chat_user_name=user_name,
                    )
            else:
                await run_generation(
                    user_id,
                    ctx["model_key"],
                    msg.text,
                    ctx_media_to_list(ctx),
                    is_chat=False,
                    chat_history_mode="once_off" if is_text_model else None,
                    chat_user_name=user_name,
                )

    @router.callback_query(F.data.in_(("tgchat_yes", "tgchat_no")))
    async def on_telegram_chat_choice(call: CallbackQuery):
        uid = call.message.chat.id
        lang = get_lang(uid)
        ctx = get_context(uid)
        if ctx.get("step") != "awaiting_telegram_chat_choice":
            await call.answer()
            return
        model_key = ctx.get("pending_chat_model_key")
        prompt = (ctx.get("pending_chat_prompt_text") or "").strip()
        model = db.get_model_by_key(model_key) if model_key else None
        if not model_key or not model or not model.is_active:
            await call.answer(
                get_text("err_model_not_found", lang).format(model_key=model_key or ""),
                show_alert=True,
            )
            clear_context(uid)
            return
        await call.answer()
        clear_context(uid)
        if call.data == "tgchat_yes":
            db.set_user_chat_mode(uid, model_key, active=True)
            cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            text_active = get_text("chat_active_msg", lang).format(model=model.name, cost=cost)
            await facade.send_message(
                uid, text_active, reply_markup=keyboards.get_chat_active_menu(lang), parse_mode="HTML"
            )
            if prompt:
                tg_uid = call.from_user.id if call.from_user else uid
                user_name_cb = (call.from_user and call.from_user.first_name) or "User"
                await flush_private_chat_async(uid, [(tg_uid, user_name_cb, prompt)])
        else:
            user_name_cb = (call.from_user and call.from_user.first_name) or "User"
            if prompt:
                await run_generation(
                    uid,
                    model_key,
                    prompt,
                    None,
                    is_chat=False,
                    chat_history_mode="once_off",
                    chat_user_name=user_name_cb,
                )
        try:
            await facade.delete_message(uid, call.message.message_id)
        except Exception:
            pass

    @router.callback_query(lambda c: bool(c.data and c.data.startswith("prompt_")))
    async def on_prompt_decision(call: CallbackQuery):
        uid = call.message.chat.id
        action = call.data.split("_")[1]
        data = pending_prompts.pop(uid, None)
        if data:
            final_prompt = data["optimized"] if action == "accept" else data["original"]
            media_list = [path_to_mediafile(p) for p in data.get("media_files", [])]
            model = db.get_model_by_key(data["model_key"])
            is_text_model = bool(model and model.type and "text" in model.type)
            if action == "accept":
                neg = (data.get("negative_prompt") or "").strip()
                if neg and model and _model_supports_negative_prompt(model):
                    ctx = dict(get_context(uid) or {})
                    options = dict(ctx.get("generation_options") or {})
                    options["negative_prompt"] = neg
                    ctx["generation_options"] = options
                    set_context(uid, ctx)
            user_name = (call.from_user and call.from_user.first_name) or "User"
            await run_generation(
                uid,
                data["model_key"],
                final_prompt,
                media_list,
                is_chat=False,
                chat_history_mode="once_off" if is_text_model else None,
                chat_user_name=user_name,
            )
            try:
                await facade.delete_message(uid, call.message.message_id)
            except Exception:
                pass
        else:
            await call.answer("Die Anfrage ist abgelaufen. Bitte starten Sie erneut.")
