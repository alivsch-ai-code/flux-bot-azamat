import time
import os
import requests
from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException
from src.utils.strings import get_text
from src.presentation.telegram.handlers.common import set_context, get_context, clear_context
from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm
from src.presentation.telegram import keyboards
from src.utils.gimmicks import get_random_tip

# --- KONFIGURATION DER MODELLE ---
MODELS_NEEDING_IMAGE = [
    "instant-id", "flux-kontext", "face-swap", 
    "ultimate-headshot-pipeline", "premium-headshot-pipeline", 
    "upscale-esrgan", "upscale-face", "google-upscaler", 
    "gemini-2.5", "qwen-image"
]

MODELS_NO_PROMPT = [
    "upscale-esrgan", "upscale-face", "google-upscaler"
]

MODELS_FORCE_DOCUMENT = [
    "upscale-esrgan", "upscale-face", "google-upscaler"
]

MODELS_OPTIONAL_IMAGE = [
    "minimax-video", "wan-2.5", "nano-banana",
    "nano-banana-pro", "gemini-2.5-flash", "gemini-2.5-flash-image"
]

pending_prompts = {}

# --- HILFSFUNKTIONEN ---

def get_user_lang(message):
    try:
        user_lang = message.from_user.language_code
        if user_lang:
            lang_code = user_lang[:2].lower()
            if lang_code in ["de", "ru", "kk"]: return lang_code
    except: pass
    return "en" 

def is_video_file(path_or_url: str) -> bool:
    if not isinstance(path_or_url, str): return False
    valid_exts = ('.mp4', '.mov', '.avi', '.webm', '.mkv')
    return path_or_url.lower().strip().endswith(valid_exts)

def is_result_url(result_item) -> bool:
    """
    Prüft, ob das Ergebnis wie eine URL aussieht (True) oder Text ist (False).
    """
    # WICHTIG: Erst in String wandeln, falls es ein Replicate-File-Objekt ist!
    result_str = str(result_item).strip()
    
    # URLs starten mit http und haben keine Leerzeichen/Zeilenumbrüche
    if result_str.startswith("http") and " " not in result_str and "\n" not in result_str:
        return True
    return False

def cleanup_previous_interaction(bot, user_id, current_msg_id=None):
    """Räumt alte User-Nachrichten und Hilfs-Nachrichten auf."""
    ctx = get_context(user_id)
    if current_msg_id:
        try: bot.delete_message(user_id, current_msg_id)
        except: pass 
    if not ctx: return
    if "cleanup_ids" in ctx:
        for msg_id in ctx["cleanup_ids"]:
            try: bot.delete_message(user_id, msg_id)
            except: pass
        del ctx["cleanup_ids"]
        set_context(user_id, ctx)

def smart_update_status(bot, user_id, text, ctx, markup=None, parse_mode="HTML"):
    """Versucht Nachricht zu editieren, sonst neu senden."""
    msg_id = ctx.get("last_bot_msg_id")
    if msg_id:
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=text,
                reply_markup=markup,
                parse_mode=parse_mode
            )
            return msg_id 
        except Exception:
            pass
    try:
        if msg_id: 
            try: bot.delete_message(user_id, msg_id)
            except: pass
        msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode=parse_mode)
        return msg.message_id
    except Exception as e:
        print(f"Status Error: {e}")
        return None


# --- HAUPTFUNKTION REGISTRIERUNG ---
def register(bot: TeleBot, generation_service, model_registry: dict, db):

    # --- BUTTON MAPPING ---
    BUTTON_TO_KEY_MAP = {}
    for key, model in model_registry.items():
        btn_text = f"{model.name} ({model.cost} ⭐️)"
        BUTTON_TO_KEY_MAP[btn_text] = key
        
    special_key = None
    if "premium-headshot-pipeline" in model_registry: special_key = "premium-headshot-pipeline"
    elif "ultimate-headshot-pipeline" in model_registry: special_key = "ultimate-headshot-pipeline"
    elif "instant-id" in model_registry: special_key = "instant-id"

    if special_key:
        model = model_registry[special_key]
        for lang_code in ["de", "en", "ru", "kk"]:
            base_text = get_text("btn_pro_headshot", lang_code)
            btn_text = f"{base_text} ({model.cost} ⭐️)"
            BUTTON_TO_KEY_MAP[btn_text] = special_key

    KNOWN_BUTTONS = list(BUTTON_TO_KEY_MAP.keys())

    # ---------------------------------------------------------
    # INTERNE FUNKTIONEN
    # ---------------------------------------------------------

    def run_generation(user_id, model_key, prompt, image_path, lang="de"):
        ctx = get_context(user_id)
        model = model_registry.get(model_key)
        if not model:
            bot.send_message(user_id, get_text("err_model_not_found", lang).format(model_key=model_key))
            return

        # 1. Guthaben prüfen
        user_credits = db.get_user_credits(user_id)
        if user_credits < model.cost:
            msg_text = get_text("err_no_credits", lang).format(cost=model.cost, balance=user_credits)
            smart_update_status(bot, user_id, msg_text, ctx)
            if image_path and os.path.exists(image_path):
                try: os.remove(image_path)
                except: pass
            clear_context(user_id)
            time.sleep(3)
            menu_msg = bot.send_message(user_id, get_text("msg_main_menu", lang), reply_markup=keyboards.get_persistent_main_menu(model_registry, lang))
            set_context(user_id, {"last_bot_msg_id": menu_msg.message_id})
            return

        # 2. Status senden
        tip = get_random_tip(lang) 
        status_text = get_text("status_generating", lang).format(model_name=model.name, tip=tip)
        
        current_msg_id = smart_update_status(bot, user_id, status_text, ctx)
        if current_msg_id:
            ctx["last_bot_msg_id"] = current_msg_id
            set_context(user_id, ctx)
        
        # Chat Action
        try:
            is_text_model = "text" in model.type if hasattr(model, "type") else False
            if "flash" in model_key or "gemini" in model_key: is_text_model = True
            action = 'typing' if is_text_model else ('upload_video' if model.type == 'video' else 'upload_photo')
            bot.send_chat_action(user_id, action)
        except Exception:
            pass

        time.sleep(1.0) 

        try:
            # 3. Service Aufruf
            success, result = generation_service.process_request(
                user_id=user_id, 
                model=model, 
                prompt=prompt, 
                image_url=image_path
            )
            
            if success:
                new_balance = db.get_user_credits(user_id)
                display_prompt = prompt if prompt not in ["Upscaling..."] else "High Resolution Upscale"

                # --- ENTSCHEIDUNG: TEXT ODER BILD? ---
                
                # Wir nehmen das erste Ergebnis
                raw_first = result[0] if isinstance(result, list) and result else result
                
                # FIX: Wir erzwingen String, um Replicate-Objekte in URLs zu wandeln
                first_item = str(raw_first)
                
                is_url = is_result_url(first_item)

                # --- FALL A: TEXT (Gemini etc.) ---
                if not is_url:
                    if current_msg_id:
                        try: bot.delete_message(user_id, current_msg_id)
                        except: pass

                    text_content = result
                    if isinstance(result, list):
                        text_content = "\n".join([str(x) for x in result])
                    
                    full_response = f"🤖 <b>{model.name}:</b>\n\n{text_content}"
                    try:
                        bot.send_message(user_id, full_response, parse_mode="Markdown")
                    except:
                        bot.send_message(user_id, full_response) # Fallback

                # --- FALL B: MEDIEN (Bilder/Videos) ---
                else:
                    if current_msg_id:
                        try: bot.delete_message(user_id, current_msg_id)
                        except: pass

                    if isinstance(result, list) and len(result) > 1: # Album
                        media_group = []
                        caption_base = get_text("success_album_caption", lang).format(
                            prompt=display_prompt, cost=model.cost, balance=new_balance
                        )
                        for i, item in enumerate(result):
                            url = str(item) # Safety cast
                            cap = caption_base if i == 0 else ""
                            media_group.append(types.InputMediaPhoto(url, caption=cap, parse_mode="HTML"))
                        try:
                            bot.send_media_group(user_id, media_group)
                        except Exception:
                            for item in result: bot.send_photo(user_id, str(item))

                    else: # Einzeldatei
                        caption_text = get_text("success_caption", lang).format(
                            prompt=display_prompt[:60], cost=model.cost, balance=new_balance
                        )
                        
                        # Die URL haben wir oben schon bereinigt
                        final_url = first_item
                        
                        # Download Fix
                        try:
                            file_content = None
                            r = requests.get(final_url)
                            if r.status_code == 200:
                                file_content = r.content
                            
                            media_to_send = file_content if file_content else final_url

                            if model.type == "video" or is_video_file(final_url):
                                bot.send_video(user_id, media_to_send, caption=caption_text, parse_mode="HTML")
                            else:
                                if model_key in MODELS_FORCE_DOCUMENT:
                                    doc_caption = caption_text + get_text("success_uncompressed", lang)
                                    bot.send_document(user_id, media_to_send, visible_file_name="result.png", caption=doc_caption, parse_mode="HTML")
                                else:
                                    bot.send_photo(user_id, media_to_send, caption=caption_text, parse_mode="HTML")
                        except Exception as e:
                            print(f"⚠️ Send Error: {e}")
                            try: bot.send_photo(user_id, final_url, caption=caption_text, parse_mode="HTML")
                            except: bot.send_message(user_id, f"Link: {final_url}")
                
                # Menü
                time.sleep(0.5)
                menu_msg = bot.send_message(
                    user_id, 
                    get_text("msg_next_step", lang), 
                    reply_markup=keyboards.get_persistent_main_menu(model_registry, lang),
                    parse_mode="HTML"
                )
                set_context(user_id, {"last_bot_msg_id": menu_msg.message_id})

            else:
                err_text = get_text("err_gen_failed", lang).format(result=result)
                smart_update_status(bot, user_id, err_text, ctx)
                time.sleep(2)
                menu_msg = bot.send_message(user_id, "Menü:", reply_markup=keyboards.get_persistent_main_menu(model_registry, lang))
                set_context(user_id, {"last_bot_msg_id": menu_msg.message_id})

        except Exception as e:
            err_text = get_text("err_critical", lang).format(error=e)
            smart_update_status(bot, user_id, err_text, ctx)
        finally:
            if image_path and os.path.exists(image_path):
                try: os.remove(image_path)
                except: pass
            if user_id in pending_prompts:
                del pending_prompts[user_id]

    # --- DEFINITION VON PROCESS_PROMPT_LOGIC ---
    def process_prompt_logic(message, ctx):
        user_id = message.chat.id
        prompt = message.text
        lang = get_user_lang(message)
        
        if ctx["model_key"] in ["premium-headshot-pipeline", "ultimate-headshot-pipeline"]:
             run_generation(user_id, ctx["model_key"], prompt, ctx.get("image_path"), lang)
             return

        loading_text = get_text("optimizing_msg", lang)
        msg_id = smart_update_status(bot, user_id, loading_text, ctx)
        if msg_id:
            ctx["last_bot_msg_id"] = msg_id
            set_context(user_id, ctx)

        try:
            optimized_prompt = optimize_prompt_via_llm(prompt)
            pending_prompts[user_id] = {
                "original": prompt,
                "optimized": optimized_prompt,
                "model_key": ctx.get("model_key"),
                "image_path": ctx.get("image_path"),
                "lang": lang 
            }
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(get_text("btn_accept", lang), callback_data="prompt_accept"),
                types.InlineKeyboardButton(get_text("btn_edit", lang), callback_data="prompt_edit"),
                types.InlineKeyboardButton(get_text("btn_reject", lang), callback_data="prompt_reject")
            )
            result_text = get_text("opt_result_msg", lang).format(original=prompt, optimized=optimized_prompt)
            if msg_id:
                bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=result_text, reply_markup=markup, parse_mode="HTML")
            else:
                 new_msg = bot.send_message(user_id, result_text, reply_markup=markup, parse_mode="HTML")
                 ctx["last_bot_msg_id"] = new_msg.message_id
                 set_context(user_id, ctx)
        except Exception:
            run_generation(user_id, ctx["model_key"], prompt, ctx.get("image_path"), lang)


    # ---------------------------------------------------------
    # HANDLER 
    # ---------------------------------------------------------

    @bot.message_handler(func=lambda msg: msg.text in KNOWN_BUTTONS)
    def handle_model_selection(message):
        user_id = message.chat.id
        lang = get_user_lang(message)
        btn_text = message.text 
        ctx = get_context(user_id)

        try: bot.delete_message(user_id, message.message_id)
        except: pass

        db.add_user_if_not_exists(user_id, message.from_user.username)
        if user_id in pending_prompts: del pending_prompts[user_id]

        internal_key = BUTTON_TO_KEY_MAP.get(btn_text)
        model = model_registry.get(internal_key)
        
        has_examples = (hasattr(model, "example_input_image") and model.example_input_image) or \
                       (hasattr(model, "example_output_image") and model.example_output_image)

        full_text = ""
        if hasattr(model, "description") and model.description:
            full_text += get_text("info_model_desc", lang).format(desc=model.description)
            if hasattr(model, "example_prompt") and model.example_prompt:
                full_text += "\n\n" + get_text("info_example_prompt", lang).format(prompt=model.example_prompt)
        if has_examples:
            full_text += f"\n\n{get_text('info_examples_disclaimer', lang)}"
        full_text += "\n\n" + ("➖" * 12) + "\n\n"
        
        cta_text = ""
        needs_image = internal_key in MODELS_NEEDING_IMAGE
        optional_image = internal_key in MODELS_OPTIONAL_IMAGE
        if internal_key in ["premium-headshot-pipeline", "ultimate-headshot-pipeline"]:
             cta_text = get_text("info_premium_pipeline", lang).format(model_name=model.name, cost=model.cost)
        elif needs_image: 
            cta_text = get_text("info_needs_image", lang).format(model_name=model.name, cost=model.cost)
        elif optional_image: 
            cta_text = get_text("info_optional_image", lang).format(model_name=model.name, cost=model.cost)
        else: 
            cta_text = get_text("info_text_only", lang).format(model_name=model.name, cost=model.cost)
        full_text += cta_text

        media_file = None
        if hasattr(model, "example_output_image") and model.example_output_image:
            media_file = model.example_output_image
        elif hasattr(model, "example_input_image") and model.example_input_image:
            media_file = model.example_input_image

        new_msg_id = None
        if media_file:
            if ctx and "last_bot_msg_id" in ctx:
                try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
                except: pass
            try:
                if is_video_file(media_file):
                    msg = bot.send_video(user_id, media_file, caption=full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                else:
                    msg = bot.send_photo(user_id, media_file, caption=full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                new_msg_id = msg.message_id
            except Exception as e:
                msg = bot.send_message(user_id, full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                new_msg_id = msg.message_id
        else:
            if ctx and "last_bot_msg_id" in ctx:
                try:
                    bot.edit_message_text(chat_id=user_id, message_id=ctx["last_bot_msg_id"], text=full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                    new_msg_id = ctx["last_bot_msg_id"] 
                except Exception:
                    try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
                    except: pass
                    msg = bot.send_message(user_id, full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                    new_msg_id = msg.message_id
            else:
                msg = bot.send_message(user_id, full_text, parse_mode="HTML", reply_markup=keyboards.get_back_menu(lang))
                new_msg_id = msg.message_id

        set_context(user_id, {
            "model_key": internal_key,
            "step": "waiting_for_image" if (needs_image or optional_image) else "waiting_for_prompt",
            "image_path": None,
            "can_skip_image": optional_image,
            "last_bot_msg_id": new_msg_id, 
            "cleanup_ids": []
        })

    @bot.message_handler(content_types=['photo'])
    def handle_image_upload(message):
        user_id = message.chat.id
        lang = get_user_lang(message)
        ctx = get_context(user_id)
        if not ctx or "waiting" not in str(ctx.get("step")): return

        loading_text = get_text("status_downloading_img", lang)
        msg_id = smart_update_status(bot, user_id, loading_text, ctx, markup=None)
        
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            if not os.path.exists("temp"): os.makedirs("temp")
            abs_path = os.path.abspath(f"temp/{user_id}_input.jpg")
            with open(abs_path, 'wb') as new_file: new_file.write(downloaded_file)

            ctx["image_path"] = abs_path
            if msg_id: ctx["last_bot_msg_id"] = msg_id 

            if ctx.get("model_key") in MODELS_NO_PROMPT:
                run_generation(user_id, ctx["model_key"], "Upscaling...", abs_path, lang)
                return

            ctx["step"] = "waiting_for_prompt"
            prompt_text = get_text("prompt_req_standard", lang)
            smart_update_status(bot, user_id, prompt_text, ctx, markup=keyboards.get_back_menu(lang))
            set_context(user_id, ctx)
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")
            clear_context(user_id)

    @bot.message_handler(func=lambda m: True) 
    def handle_prompt_input_step(message):
        user_id = message.chat.id
        prompt = message.text
        
        back_btns = [get_text("btn_back", code) for code in ["en", "de", "ru", "kk"]]
        if prompt in back_btns or (prompt and prompt.startswith("/")): return

        if prompt in KNOWN_BUTTONS:
            handle_model_selection(message)
            return
            
        ctx = get_context(user_id)
        if not ctx or not ctx.get("model_key"): return 
        
        if ctx.get("step") == "waiting_for_image" and not ctx.get("can_skip_image"):
            bot.send_message(user_id, get_text("err_img_missing", get_user_lang(message)))
            return

        process_prompt_logic(message, ctx)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('prompt_'))
    def handle_prompt_decision(call):
        user_id = call.message.chat.id
        data = pending_prompts.get(user_id)
        lang = data.get('lang', 'de') if data else 'de'

        if not data:
            bot.answer_callback_query(call.id, get_text("session_expired", lang))
            return

        action = call.data.split('_')[1]

        if action == "accept":
            bot.answer_callback_query(call.id, "✅")
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
            run_generation(user_id, data['model_key'], data['optimized'], data['image_path'], lang)
        elif action == "reject":
            bot.answer_callback_query(call.id, "❌")
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
            run_generation(user_id, data['model_key'], data['original'], data['image_path'], lang)
        elif action == "edit":
            bot.answer_callback_query(call.id, "✏️")
            msg_text = get_text("msg_copy_edit", lang).format(optimized=data['optimized'])
            msg = bot.send_message(user_id, msg_text, parse_mode="HTML")
            
            def edit_step(m):
                try: bot.delete_message(user_id, m.message_id)
                except: pass
                try: bot.delete_message(user_id, msg.message_id)
                except: pass
                run_generation(user_id, data['model_key'], m.text, data['image_path'], lang)
            bot.register_next_step_handler(msg, edit_step)