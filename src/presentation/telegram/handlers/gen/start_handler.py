"""
start_handler.py – Start-Generierung (async, aiogram).
"""

from __future__ import annotations

from typing import Optional

from aiogram import F
from aiogram.types import CallbackQuery

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.gen.media_helpers import (
    schema_allows_multiple_media,
    schema_requires_media,
)
from src.presentation.telegram.handlers.gen.ux import smart_update_status
from src.utils.strings import get_text


async def do_start_gen_flow(
    facade,
    user_id: int,
    model_key: str,
    db,
    get_lang,
    edit_message_id: Optional[int] = None,
    pending_webapp_prompt: Optional[str] = None,
) -> bool:
    model = db.get_model_by_key(model_key)
    if not model or not model.is_active:
        return False
    lang = get_lang(user_id)
    prev = get_context(user_id) or {}
    existing_media = prev.get("media_paths") or []
    generation_options = prev.get("generation_options") or {}
    has_media = bool(existing_media)
    needs_media = schema_requires_media(model.input_schema, model=model)
    step = "waiting_for_prompt" if has_media else ("waiting_for_media" if needs_media else "waiting_for_prompt")

    ctx_payload = {
        "model_key": model_key,
        "step": step,
        "media_paths": existing_media if has_media else [],
        "generation_options": generation_options,
        "last_bot_msg_id": edit_message_id,
        "menu_path": model.menu_path,
    }
    if pending_webapp_prompt and pending_webapp_prompt.strip():
        ctx_payload["pending_webapp_prompt"] = pending_webapp_prompt.strip()
    set_context(user_id, ctx_payload)
    if step == "waiting_for_media":
        allow_multi = schema_allows_multiple_media(model.input_schema)
        prompt_text = get_text("model_req_media_multiple", lang) if allow_multi else get_text("model_req_media_single", lang)
    else:
        prompt_text = get_text("model_req_prompt", lang)
    if model.example_data and model.example_data.get("prompt") and step == "waiting_for_prompt":
        prompt_text += f"\n\n📝 Bsp: <code>{model.example_data.get('prompt')[:100]}...</code>"
    markup = keyboards.get_back_menu(lang, target=f"sel_{model_key}")

    if edit_message_id:
        ctx = {"last_bot_msg_id": edit_message_id}
        new_id = await smart_update_status(facade, user_id, prompt_text, ctx, markup)
    else:
        msg = await facade.send_message(
            user_id, prompt_text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False
        )
        new_id = msg.message_id
    ctx = dict(get_context(user_id) or {})
    ctx["last_bot_msg_id"] = new_id
    set_context(user_id, ctx)
    return True


def register_start_gen_handler(router, facade, db, get_lang) -> None:
    @router.callback_query(F.data.startswith("start_gen_"))
    async def handle_start_gen(call: CallbackQuery):
        key = call.data.split("start_gen_")[1]
        user_id = call.message.chat.id
        await do_start_gen_flow(
            facade, user_id, key, db, get_lang, edit_message_id=call.message.message_id
        )
        try:
            await call.answer()
        except Exception:
            pass
