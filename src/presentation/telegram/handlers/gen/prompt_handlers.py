"""
prompt_handlers.py – Text-Prompt und Optimierung

Registriert:
- on_prompt (message_handler): Empfängt Text. Bei Chat-Modus → run_generation. Bei waiting_for_prompt:
  optional Optimierung via LLM, dann pending_prompts speichern oder direkt run_generation.
- on_prompt_decision (callback): prompt_accept/prompt_reject → run_generation mit optimiertem oder Original-Prompt.
"""

import time

from telebot import types

from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm
from src.presentation.telegram.handlers.common import get_context
from src.presentation.telegram.handlers.gen import (
    cleanup_pending_prompts,
    ctx_media_to_list,
    path_to_mediafile,
    pending_prompts,
)
from src.presentation.telegram.handlers.gen.chat_sessions import (
    append_with_summary_if_needed,
    build_chat_prompt_from_messages,
)
from src.utils.strings import get_text


def register_prompt_handlers(bot, db, get_lang, run_generation) -> None:
    """Registriert on_prompt und on_prompt_decision."""

    @bot.message_handler(func=lambda m: True)
    def on_prompt(msg):
        user_id = msg.chat.id
        ctx = get_context(user_id)

        # 1) Chat-Modus: LLM-Chat mit persistenter History
        chat_state = None
        try:
            chat_state = db.get_user_chat_state(user_id)
        except Exception:
            chat_state = None

        if chat_state and chat_state.get("is_chat") and chat_state.get("model_key"):
            model_key = chat_state["model_key"]
            model = db.get_model_by_key(model_key)
            is_text_model = bool(model and model.type and "text" in model.type)

            if is_text_model:
                try:
                    user_name = (msg.from_user and msg.from_user.first_name) or "User"
                    messages = append_with_summary_if_needed(
                        db,
                        user_id,
                        model_key,
                        {"role": "user", "content": msg.text, "user_name": user_name},
                    )
                    lang = get_lang(user_id)
                    sys_prompt = get_text("azamat_private_chat_prompt", lang)
                    sys_prompt = f"{sys_prompt}\n\n{get_text('azamat_user_name_hint', lang).format(name=user_name)}"
                    full_prompt = build_chat_prompt_from_messages(messages, msg.text, system_prompt=sys_prompt, current_user_name=user_name)
                    run_generation(
                        user_id,
                        model_key,
                        full_prompt,
                        media_files=None,
                        is_chat=True,
                        chat_history_mode="persistent",
                        chat_user_name=user_name,
                    )
                except Exception:
                    # Wenn History-Build scheitert: trotzdem antworten und History via runner neu aufbauen.
                    run_generation(
                        user_id,
                        model_key,
                        msg.text,
                        media_files=None,
                        is_chat=True,
                        chat_history_mode="once_off",
                        chat_user_name=(msg.from_user and msg.from_user.first_name) or "User",
                    )
            else:
                run_generation(user_id, model_key, msg.text, media_files=None, is_chat=True)
            return

        # 2) Reine Text-Nachricht im Hauptmenü: Default-Chatmodell starten
        # Nur wenn kein aktiver Gen-Context existiert.
        if not ctx:
            try:
                default_model_key = "google-gemini-2-5-flash"  # entspricht replicate_id google/gemini-2.5-flash
                model = db.get_model_by_key(default_model_key)
                if model and model.type and "text" in model.type:
                    db.set_user_chat_mode(user_id, default_model_key, active=True)
                    user_name = (msg.from_user and msg.from_user.first_name) or "User"
                    messages = append_with_summary_if_needed(
                        db,
                        user_id,
                        default_model_key,
                        {"role": "user", "content": msg.text, "user_name": user_name},
                    )
                    lang = get_lang(user_id)
                    sys_prompt = get_text("azamat_private_chat_prompt", lang)
                    sys_prompt = f"{sys_prompt}\n\n{get_text('azamat_user_name_hint', lang).format(name=user_name)}"
                    full_prompt = build_chat_prompt_from_messages(messages, msg.text, system_prompt=sys_prompt, current_user_name=user_name)
                    run_generation(
                        user_id,
                        default_model_key,
                        full_prompt,
                        media_files=None,
                        is_chat=True,
                        chat_history_mode="persistent",
                        chat_user_name=user_name,
                    )
                    return
            except Exception:
                # Fallback: Durchlaufen in den normalen Flow (z.B. Menü-Handler)
                pass
        if ctx and ctx.get("step") == "waiting_for_prompt":
            model = db.get_model_by_key(ctx["model_key"])
            is_text_model = bool(model and model.type and "text" in model.type)
            settings = db.get_user_settings(user_id)
            user_name = (msg.from_user and msg.from_user.first_name) or "User"
            if settings.get("auto_opt", True):
                msg_wait = bot.send_message(user_id, get_text("optimizing_msg", get_lang(user_id)), parse_mode="HTML")
                try:
                    optimized = optimize_prompt_via_llm(msg.text)
                    pending_prompts[user_id] = {"original": msg.text, "optimized": optimized, "model_key": ctx["model_key"], "media_files": ctx.get("media_paths", []), "timestamp": time.time()}
                    cleanup_pending_prompts()
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton(get_text("btn_accept", get_lang(user_id)), callback_data="prompt_accept"),
                        types.InlineKeyboardButton(get_text("btn_reject", get_lang(user_id)), callback_data="prompt_reject")
                    )
                    bot.edit_message_text(get_text("opt_result_msg", get_lang(user_id)).format(original=msg.text, optimized=optimized), user_id, msg_wait.message_id, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    run_generation(
                        user_id,
                        ctx["model_key"],
                        msg.text,
                        ctx_media_to_list(ctx),
                        is_chat=False,
                        chat_history_mode="once_off" if is_text_model else None,
                        chat_user_name=user_name,
                    )
            else:
                run_generation(
                    user_id,
                    ctx["model_key"],
                    msg.text,
                    ctx_media_to_list(ctx),
                    is_chat=False,
                    chat_history_mode="once_off" if is_text_model else None,
                    chat_user_name=user_name,
                )

    @bot.callback_query_handler(func=lambda c: c.data.startswith('prompt_'))
    def on_prompt_decision(call):
        uid = call.message.chat.id
        action = call.data.split('_')[1]
        data = pending_prompts.pop(uid, None)
        if data:
            final_prompt = data["optimized"] if action == "accept" else data["original"]
            media_list = [path_to_mediafile(p) for p in data.get("media_files", [])]
            model = db.get_model_by_key(data["model_key"])
            is_text_model = bool(model and model.type and "text" in model.type)
            user_name = (call.message.from_user and call.message.from_user.first_name) or "User"
            run_generation(
                uid,
                data["model_key"],
                final_prompt,
                media_list,
                is_chat=False,
                chat_history_mode="once_off" if is_text_model else None,
                chat_user_name=user_name,
            )
            try:
                bot.delete_message(uid, call.message.message_id)
            except Exception:
                pass
        else:
            bot.answer_callback_query(call.id, "Die Anfrage ist abgelaufen. Bitte starten Sie erneut.")
