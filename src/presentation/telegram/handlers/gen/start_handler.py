"""
start_handler.py – Start-Generierung Handler

Registriert handle_start_gen (start_gen_*): User klickt auf „Start“ bei einem Modell.
- Prüft, ob Modell Media benötigt (schema_requires_media, img2img, upscale)
- Setzt Context auf waiting_for_media oder waiting_for_prompt
- Fordert entsprechend Media oder Prompt an (model_req_media / model_req_prompt)
- Aktualisiert die Nachricht via smart_update_status
"""

from typing import Optional

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.gen.media_helpers import (
    schema_allows_multiple_media,
    schema_requires_media,
)
from src.presentation.telegram.handlers.gen.ux import smart_update_status
from src.utils.strings import get_text


def do_start_gen_flow(bot, user_id: int, model_key: str, db, get_lang, edit_message_id: Optional[int] = None) -> bool:
    """
    Startet den Generierungs-Flow (Context setzen, Prompt/Media anfordern).
    edit_message_id: Falls gesetzt, wird die Nachricht editiert; sonst wird neu gesendet.
    Wird von WebApp (process_webapp_action) und Callback (handle_start_gen) genutzt.
    """
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

    set_context(
        user_id,
        {
            "model_key": model_key,
            "step": step,
            "media_paths": existing_media if has_media else [],
            "generation_options": generation_options,
            "last_bot_msg_id": edit_message_id,
            "menu_path": model.menu_path,
        },
    )
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
        new_id = smart_update_status(bot, user_id, prompt_text, ctx, markup)
    else:
        msg = bot.send_message(user_id, prompt_text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
        new_id = msg.message_id
    ctx = dict(get_context(user_id) or {})
    ctx["last_bot_msg_id"] = new_id
    set_context(user_id, ctx)
    return True


def register_start_gen_handler(bot, db, get_lang) -> None:
    """Registriert den handle_start_gen Callback-Handler."""

    @bot.callback_query_handler(func=lambda c: c.data.startswith('start_gen_'))
    def handle_start_gen(call):
        key = call.data.split('start_gen_')[1]
        user_id = call.message.chat.id
        do_start_gen_flow(bot, user_id, key, db, get_lang, edit_message_id=call.message.message_id)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
