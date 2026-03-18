"""
start_handler.py – Start-Generierung Handler

Registriert handle_start_gen (start_gen_*): User klickt auf „Start“ bei einem Modell.
- Prüft, ob Modell Media benötigt (schema_requires_media, img2img, upscale)
- Setzt Context auf waiting_for_media oder waiting_for_prompt
- Fordert entsprechend Media oder Prompt an (model_req_media / model_req_prompt)
- Aktualisiert die Nachricht via smart_update_status
"""

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.gen.media_helpers import schema_requires_media
from src.presentation.telegram.handlers.gen.ux import smart_update_status
from src.utils.strings import get_text


def register_start_gen_handler(bot, db, get_lang) -> None:
    """Registriert den handle_start_gen Callback-Handler."""

    @bot.callback_query_handler(func=lambda c: c.data.startswith('start_gen_'))
    def handle_start_gen(call):
        key = call.data.split('start_gen_')[1]
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        model = db.get_model_by_key(key)
        prev = get_context(user_id) or {}
        existing_media = prev.get("media_paths") or []
        has_media = bool(existing_media)

        needs_media = schema_requires_media(model.input_schema) or (model.type and ("img2img" in model.type or "upscale" in model.type))
        # Wenn der User bereits ein Medium hochgeladen hat (Hauptmenü-Fallback), fragen wir NICHT erneut nach Upload.
        step = "waiting_for_prompt" if has_media else ("waiting_for_media" if needs_media else "waiting_for_prompt")

        set_context(
            user_id,
            {
                "model_key": key,
                "step": step,
                "media_paths": existing_media if has_media else [],
                "last_bot_msg_id": call.message.message_id,
                "menu_path": model.menu_path,
            },
        )
        prompt_text = get_text("model_req_media", lang) if step == "waiting_for_media" else get_text("model_req_prompt", lang)
        if model.example_data and model.example_data.get("prompt") and step == "waiting_for_prompt":
            prompt_text += f"\n\n📝 Bsp: <code>{model.example_data.get('prompt')[:100]}...</code>"
        markup = keyboards.get_back_menu(lang, target=f"sel_{key}")
        smart_update_status(bot, user_id, prompt_text, {"last_bot_msg_id": call.message.message_id}, markup)
