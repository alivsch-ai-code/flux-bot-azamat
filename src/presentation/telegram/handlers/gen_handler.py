import time
import os
import logging
import uuid
from telebot import TeleBot, types
from src.utils.strings import get_text
from src.presentation.telegram.handlers.common import set_context, get_context, clear_context
from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm
from src.presentation.telegram import keyboards
from src.utils.gimmicks import get_random_tip

logger = logging.getLogger(__name__)

# Speicher für Prompt-Optimierungen mit Timeout
pending_prompts = {}
PROMPT_TIMEOUT = 300  # 5 Minuten Timeout für Prompt-Entscheidung

def cleanup_pending_prompts():
    """Entfernt abgelaufene Prompt-Einträge."""
    now = time.time()
    expired = [uid for uid, data in pending_prompts.items() 
               if now - data.get("timestamp", 0) > PROMPT_TIMEOUT]
    for uid in expired:
        pending_prompts.pop(uid, None)
        logger.info(f"Prompt-Entscheidung für User {uid} timeout")

def smart_update_status(bot, user_id, text, ctx, markup=None):
    """
    Versucht eine Nachricht zu bearbeiten, sendet neu falls nicht möglich.
    """
    msg_id = ctx.get("last_bot_msg_id")
    try:
        if msg_id:
            bot.edit_message_text(text, user_id, msg_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
            return msg_id
        else:
            msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
            return msg.message_id
    except Exception as e:
        logger.warning(f"Edit failed for user {user_id}, sending new message: {e}")
        msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
        return msg.message_id

def _is_technical_error(error_msg: str) -> bool:
    if not error_msg: return False
    err = str(error_msg).lower()
    if any(x in err for x in ["credits", "guthaben", "nsfw", "safety", "bildqualität", "resolution"]): return False
    return True

def register(bot: TeleBot, generation_service, model_registry, db):

    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]

    # --- 1. NAVIGATION DURCH KATEGORIEN ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith('nav_path_'))
    def handle_path_nav(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        target_path = call.data.replace("nav_path_", "")

        all_models = db.get_all_models()
        markup = keyboards.get_dynamic_model_menu(all_models, lang, target_path)

        title_key = f"title_{target_path.replace('/', '_')}"
        title_text = get_text(title_key, lang)

        if title_text == title_key:
            cat_name = target_path.split("/")[-1].capitalize()
            display_name = get_text(f"menu_{cat_name.lower()}", lang)
            if display_name.startswith("menu_"): display_name = cat_name
            title_text = f"📂 <b>{display_name}</b>"

        try:
            bot.edit_message_text(title_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Edit failed in handle_path_nav: {e}")
            bot.send_message(user_id, title_text, reply_markup=markup, parse_mode="HTML")

    # --- 2. MODELL AUSWAHL (DETAIL VIEW) ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_model_click(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        key = call.data.split('sel_')[1]

        model = db.get_model_by_key(key)
        if not model or not model.is_active:
            bot.answer_callback_query(call.id, get_text("err_model_maintenance", lang) or "⚠️ Inactive.")
            return

        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)

        # A) TEXT MODELLE (Chat Modus Abfrage)
        if model.type and "text" in model.type:
            text = get_text("ask_chat_mode", lang).format(cost=final_cost)
            # Nutzt keyboards.get_chat_mode_ask_menu -> erzeugt 'chat_mode_yes_...' / 'chat_mode_no_...'
            markup = keyboards.get_chat_mode_ask_menu(key, lang)
            bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        # B) GENERATION MODELLE
        preview_link = ""
        if model.example_data and isinstance(model.example_data, dict):
            url = model.example_data.get("output_image") or model.example_data.get("image") or model.example_data.get("url")
            if url and str(url).startswith("http"):
                preview_link = f"<a href='{url}'>&#8205;</a>" # Zero-Width-Space Link

        text = f"{preview_link}🤖 <b>{model.name}</b>\n"
        text += f"{model.description}\n\n"
        text += f"💰 <b>Kosten: {final_cost} Credits</b>"

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"🚀 Start ({final_cost} Credits)", callback_data=f"start_gen_{key}"))
        if model.input_schema:
            markup.add(types.InlineKeyboardButton("⚙️ Settings", callback_data=f"settings_{key}"))

        back_target = f"nav_path_{model.menu_path}"
        markup.add(types.InlineKeyboardButton(get_text("btn_back", lang), callback_data=back_target))

        bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)

    # --- 3. NEU: CHAT MODUS ENTSCHEIDUNG ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith('chat_mode_'))
    def handle_chat_decision(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        data = call.data

        # Entscheidung parsen
        if "chat_mode_yes_" in data:
            action = "yes"
            key = data.replace("chat_mode_yes_", "")
        else:
            action = "no"
            key = data.replace("chat_mode_no_", "")

        model = db.get_model_by_key(key)
        if not model:
            bot.answer_callback_query(call.id, "Model error")
            return

        final_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)

        if action == "yes":
            # 1. Chat Modus aktivieren
            db.set_user_chat_mode(user_id, key, active=True)

            text = get_text("chat_active_msg", lang).format(model=model.name, cost=final_cost)
            markup = keyboards.get_chat_active_menu(lang)

            bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

        else:
            # 2. Einmaliger Prompt (Chat Modus aus)
            db.set_user_chat_mode(user_id, None, active=False)

            set_context(user_id, {
                "model_key": key,
                "step": "waiting_for_prompt",
                "last_bot_msg_id": call.message.message_id,
                "menu_path": model.menu_path
            })

            prompt_text = get_text("model_req_prompt", lang)
            markup = keyboards.get_back_menu(lang, target=f"sel_{key}")

            bot.edit_message_text(prompt_text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

        try: bot.answer_callback_query(call.id)
        except Exception as e:
            logger.warning(f"answer_callback_query failed: {e}")

    # --- 4. NEU: CHAT STOPPEN ---
    @bot.callback_query_handler(func=lambda c: c.data == 'stop_chat')
    def handle_stop_chat(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)

        db.set_user_chat_mode(user_id, None, active=False)

        try: bot.answer_callback_query(call.id, get_text("chat_ended", lang))
        except Exception as e:
            logger.warning(f"answer_callback_query failed in stop_chat: {e}")

        # Zurück zum Hauptmenü
        all_models = db.get_all_models()
        markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
        text = get_text("welcome", lang)

        try:
            bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Edit failed in stop_chat: {e}")
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")

    # --- 5. START TRIGGER (BILD GENERIERUNG) ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith('start_gen_'))
    def handle_start_gen(call):
        key = call.data.split('start_gen_')[1]
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        model = db.get_model_by_key(key)

        input_keys = model.input_schema.keys() if model.input_schema else []
        step = "waiting_for_image" if ("image" in input_keys or (model.type and "img2img" in model.type)) else "waiting_for_prompt"

        set_context(user_id, {
            "model_key": key, "step": step,
            "last_bot_msg_id": call.message.message_id,
            "menu_path": model.menu_path
        })

        prompt_text = get_text("model_req_image", lang) if step == "waiting_for_image" else get_text("model_req_prompt", lang)

        if model.example_data and model.example_data.get("prompt") and step == "waiting_for_prompt":
            prompt_text += f"\n\n📝 Bsp: <code>{model.example_data.get('prompt')[:100]}...</code>"

        markup = keyboards.get_back_menu(lang, target=f"sel_{key}")
        smart_update_status(bot, user_id, prompt_text, {"last_bot_msg_id": call.message.message_id}, markup)

    # --- 6. GENERATION ENGINE ---
    def run_generation(user_id, model_key, prompt, image_path, is_chat=False):
        ctx = get_context(user_id)
        lang = get_lang(user_id)
        model = db.get_model_by_key(model_key)

        if not model:
            logger.error(f"Model {model_key} not found for user {user_id}")
            return

        try:
            cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            user_credits = int(db.get_user_credits(user_id))

            if user_credits < cost:
                smart_update_status(bot, user_id, get_text("err_no_credits", lang), ctx)
                return

            wait_msg_id = smart_update_status(bot, user_id, get_text("status_generating", lang).format(tip=get_random_tip(lang)), ctx)
            bot.send_chat_action(user_id, 'typing' if is_chat else 'upload_photo')

            success, result = generation_service.process_request(user_id, model, prompt, image_path)

            # Fallback Logik
            if not success and _is_technical_error(result):
                fallback_model = db.get_fallback_model(model)
                if fallback_model:
                    logger.info(f"Fallback von {model.name} zu {fallback_model.name} für User {user_id}")
                    smart_update_status(bot, user_id, get_text("fallback_attempt", lang).format(model=model.name, fallback=fallback_model.name), ctx)
                    success, result = generation_service.process_request(user_id, fallback_model, prompt, image_path)
                    if success:
                        model = fallback_model
                        cost = int(model.custom_price or model.internal_cost)
                else:
                    logger.warning(f"Kein Fallback-Modell verfügbar für {model.name}")

            try: bot.delete_message(user_id, wait_msg_id)
            except Exception as e:
                logger.debug(f"Delete wait message failed: {e}")

            if success:
                res = str(result[0]) if isinstance(result, list) else str(result)
                if is_chat:
                    bot.send_message(user_id, res, reply_markup=keyboards.get_chat_active_menu(lang))
                else:
                    caption = get_text("success_caption", lang).format(prompt=prompt[:50], cost=cost)
                    try:
                        if model.type and "video" in model.type:
                            bot.send_video(user_id, res, caption=caption)
                        elif model.type and "audio" in model.type:
                            bot.send_audio(user_id, res, caption=caption)
                        elif model.type and "image" in model.type:
                            bot.send_photo(user_id, res, caption=caption)
                        else:
                            bot.send_message(user_id, f"{res}\n\n💰 {cost} Credits")
                    except Exception as e:
                        logger.error(f"Send media failed for user {user_id}: {e}")
                        bot.send_message(user_id, f"{res}\n\n💰 {cost} Credits")

                    time.sleep(1)
                    next_markup = keyboards.get_dynamic_model_menu(db.get_all_models(), lang, ctx.get("menu_path", "root"))
                    bot.send_message(user_id, get_text("msg_next_step", lang), reply_markup=next_markup, parse_mode="HTML")
            else:
                logger.error(f"Generation failed for user {user_id}: {result}")
                smart_update_status(bot, user_id, get_text("err_gen_failed", lang).format(result=result), ctx)

        except Exception as e:
            logger.exception(f"System Error in run_generation for user {user_id}: {e}")
            smart_update_status(bot, user_id, f"System Error: {str(e)}", ctx)
        finally:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {image_path}: {e}")
            if not is_chat:
                clear_context(user_id)

    # --- 7. INPUT LISTENER (PROMPT) ---
    @bot.message_handler(func=lambda m: True)
    def on_prompt(msg):
        user_id = msg.chat.id
        ctx = get_context(user_id)

        # A) Chat Modus Check (DB)
        try:
            chat_state = db.get_user_chat_state(user_id)
            if chat_state and chat_state.get("is_chat") and chat_state.get("model_key"):
                run_generation(user_id, chat_state["model_key"], msg.text, None, is_chat=True)
                return
        except Exception as e:
            logger.warning(f"get_user_chat_state failed for user {user_id}: {e}")

        # B) Normaler Flow
        if ctx and ctx.get("step") == "waiting_for_prompt":
            settings = db.get_user_settings(user_id)
            if settings.get("auto_opt", True):
                msg_wait = bot.send_message(user_id, get_text("optimizing_msg", get_lang(user_id)), parse_mode="HTML")
                try:
                    optimized = optimize_prompt_via_llm(msg.text)
                    pending_prompts[user_id] = {
                        "original": msg.text,
                        "optimized": optimized,
                        "model_key": ctx["model_key"],
                        "image_path": ctx.get("image_path"),
                        "timestamp": time.time()
                    }
                    cleanup_pending_prompts()  # Aufräumen beim Speichern
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton(get_text("btn_accept", get_lang(user_id)), callback_data="prompt_accept"),
                        types.InlineKeyboardButton(get_text("btn_reject", get_lang(user_id)), callback_data="prompt_reject")
                    )
                    bot.edit_message_text(get_text("opt_result_msg", get_lang(user_id)).format(original=msg.text, optimized=optimized),
                                        user_id, msg_wait.message_id, reply_markup=markup, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Prompt optimization failed for user {user_id}: {e}, using original prompt")
                    run_generation(user_id, ctx["model_key"], msg.text, ctx.get("image_path"))
            else:
                run_generation(user_id, ctx["model_key"], msg.text, ctx.get("image_path"))

    @bot.callback_query_handler(func=lambda c: c.data.startswith('prompt_'))
    def on_prompt_decision(call):
        uid = call.message.chat.id
        action = call.data.split('_')[1]
        data = pending_prompts.pop(uid, None)
        if data:
            final_prompt = data['optimized'] if action == "accept" else data['original']
            run_generation(uid, data['model_key'], final_prompt, data['image_path'])
            try: bot.delete_message(uid, call.message.message_id)
            except Exception as e:
                logger.debug(f"Delete prompt decision message failed: {e}")
        else:
            logger.warning(f"No pending prompt found for user {uid}")
            bot.answer_callback_query(call.id, "Die Anfrage ist abgelaufen. Bitte starten Sie erneut.")

    @bot.message_handler(content_types=['photo'])
    def on_image(msg):
        user_id = msg.chat.id
        ctx = get_context(user_id)
        if ctx and ctx.get("step") == "waiting_for_image":
            try:
                file_info = bot.get_file(msg.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                # Unique filename mit UUID und cleanup alter Dateien
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Alte Temp-Dateien des Users löschen
                for f in os.listdir(temp_dir):
                    if f.startswith(f"user_{user_id}_"):
                        try:
                            os.remove(os.path.join(temp_dir, f))
                        except Exception as e:
                            logger.warning(f"Failed to delete old temp file {f}: {e}")
                
                path = os.path.join(temp_dir, f"user_{user_id}_{uuid.uuid4().hex[:8]}.jpg")
                with open(path, 'wb') as f:
                    f.write(downloaded_file)

                ctx["image_path"] = path
                ctx["step"] = "waiting_for_prompt"

                model = db.get_model_by_key(ctx["model_key"])
                if model and model.type and "upscale" in model.type:
                    run_generation(user_id, ctx["model_key"], "", path)
                else:
                    lang = get_lang(user_id)
                    bot.send_message(user_id, "✅ Bild erhalten! " + get_text("model_req_prompt", lang),
                                   reply_markup=keyboards.get_back_menu(lang, f"sel_{ctx['model_key']}"), parse_mode="HTML")
                    set_context(user_id, ctx)
            except Exception as e:
                logger.exception(f"Image upload failed for user {user_id}: {e}")
                bot.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
