import time
import os
from telebot import TeleBot, types
from src.utils.strings import get_text
from src.presentation.telegram.handlers.common import set_context, get_context, clear_context
from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm
from src.presentation.telegram import keyboards
from src.utils.gimmicks import get_random_tip

# --- CONFIG ---
MODELS_NEEDING_IMAGE = [
    "instant-id", "flux-kontext", "face-swap", 
    "ultimate-headshot-pipeline", "premium-headshot-pipeline", 
    "upscale-esrgan", "upscale-face", "google-upscaler", "gemini-2.5", "qwen-image",
    "vid2audio" 
]
MODELS_NO_PROMPT = ["upscale-esrgan", "upscale-face", "google-upscaler"]
pending_prompts = {}

def smart_update_status(bot, user_id, text, ctx, markup=None):
    """
    Intelligentes Update: Versucht Nachricht zu editieren oder sendet neu.
    """
    msg_id = ctx.get("last_bot_msg_id")
    try:
        if msg_id:
            bot.edit_message_text(text, user_id, msg_id, reply_markup=markup, parse_mode="HTML")
            return msg_id
        else:
            msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
            return msg.message_id
    except:
        msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return msg.message_id

def register(bot: TeleBot, generation_service, model_registry: dict, db):

    def get_lang(uid): return db.get_user_settings(uid)["lang"]

    def run_generation(user_id, model_key, prompt, image_path):
        ctx = get_context(user_id)
        lang = get_lang(user_id)
        
        model = model_registry.get(model_key)
        if not model:
            bot.send_message(user_id, f"⚠️ Backend für {model_key} noch nicht verbunden.")
            return
        user_credits = int(db.get_user_credits(user_id))
        model_cost = int(model.cost)

        if user_credits < model_cost:
            msg = get_text("err_no_credits", lang)
            smart_update_status(bot, user_id, msg, ctx)
            clear_context(user_id)
            return

        smart_update_status(bot, user_id, get_text("status_generating", lang).format(tip=get_random_tip(lang)), ctx)
        
        try:
            bot.send_chat_action(user_id, 'upload_photo')
            success, result = generation_service.process_request(user_id, model, prompt, image_path)
            
            if success:
                res = str(result[0]) if isinstance(result, list) else str(result)
                
                if "last_bot_msg_id" in ctx:
                    try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
                    except: pass

                if res.startswith("http"):
                    caption = get_text("success_caption", lang).format(prompt=prompt[:40], cost=model.cost)
                    try:
                        if "video" in str(model.type): bot.send_video(user_id, res, caption=caption)
                        elif "audio" in str(model.type): bot.send_audio(user_id, res, caption=caption)
                        else: bot.send_photo(user_id, res, caption=caption)
                    except: bot.send_message(user_id, res)
                else:
                    bot.send_message(user_id, res) 
                
                time.sleep(1)
                bot.send_message(user_id, get_text("msg_next_step", lang), reply_markup=keyboards.get_main_menu_inline(lang), parse_mode="HTML")
            else:
                smart_update_status(bot, user_id, get_text("err_gen_failed", lang).format(result=result), ctx)
        except Exception as e:
            smart_update_status(bot, user_id, str(e), ctx)
        finally:
            if image_path and os.path.exists(image_path): os.remove(image_path)
            clear_context(user_id)

    def process_prompt_logic(message, ctx):
        user_id = message.chat.id
        prompt = message.text
        lang = get_lang(user_id)
        settings = db.get_user_settings(user_id)

        if "last_bot_msg_id" in ctx:
             try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
             except: pass

        status_text = get_text("optimizing_msg", lang) if settings.get("auto_opt", True) else "🚀..."
        msg = bot.send_message(user_id, status_text, parse_mode="HTML")
        
        ctx["last_bot_msg_id"] = msg.message_id
        set_context(user_id, ctx)

        if settings.get("auto_opt", True):
            try:
                optimized = optimize_prompt_via_llm(prompt)
                pending_prompts[user_id] = {
                    "original": prompt, "optimized": optimized, 
                    "model_key": ctx["model_key"], "image_path": ctx.get("image_path")
                }
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton(get_text("btn_accept", lang), callback_data="prompt_accept"),
                    types.InlineKeyboardButton(get_text("btn_edit", lang), callback_data="prompt_edit"),
                    types.InlineKeyboardButton(get_text("btn_reject", lang), callback_data="prompt_reject")
                )
                
                res_txt = get_text("opt_result_msg", lang).format(original=prompt, optimized=optimized)
                smart_update_status(bot, user_id, res_txt, ctx, markup)
            except:
                run_generation(user_id, ctx["model_key"], prompt, ctx.get("image_path"))
        else:
            run_generation(user_id, ctx["model_key"], prompt, ctx.get("image_path"))

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_model_click(call):
        user_id = call.message.chat.id
        lang = get_lang(user_id)
        key = call.data.split('_')[1]
        
        model = model_registry.get(key)
        if not model:
            print("NO MODELL CLICKED")
            class DummyModel:
                name = key.upper(); description = "Model"; cost = 5; type = ["image"]
                example_prompt=None; example_output_image=None
            model = DummyModel()

        # 1. Textbausteine vorbereiten
        title_text = get_text("model_info_title", lang).format(name=model.name, desc=model.description, cost=model.cost)
        
        example_text = ""
        if model.example_prompt or model.example_output_image:
            example_text += "\n\n" + get_text("model_example_intro", lang)
            if model.example_prompt:
                example_text += f"\n\n📝 <i>Prompt:</i>\n<code>{model.example_prompt}</code>"

        req_text = get_text("model_req_image", lang) if key in MODELS_NEEDING_IMAGE else get_text("model_req_prompt", lang)
        
        # Gesamter Text für die Nachricht / Caption
        full_info_text = title_text + example_text + req_text

        # 2. Navigation bestimmen
        back = "nav_image"
        if "audio" in str(model.type) or "tts" in key: back = "nav_audio"
        elif "video" in str(model.type): back = "nav_video"
        reply_markup = keyboards.get_back_menu(lang, target=back)

        # 3. AUSGABE-LOGIK (LOKALES BILD VS TEXT)
        img_path = str(model.example_output_image) if model.example_output_image else None
        
        if img_path and not img_path.startswith("http") and os.path.exists(img_path):
            # Lösche die Menü-Nachricht und sende Bild mit Text als Caption
            try: bot.delete_message(user_id, call.message.message_id)
            except: pass
            
            with open(img_path, 'rb') as photo:
                sent_msg = bot.send_photo(
                    user_id, 
                    photo, 
                    caption=full_info_text, 
                    parse_mode="HTML", 
                    reply_markup=reply_markup
                )
            set_context(user_id, {"model_key": key, "step": "waiting_for_prompt", "last_bot_msg_id": sent_msg.message_id})
        else:
            # Normales Editieren, falls kein lokales Bild vorhanden ist (oder URL genutzt wird)
            display_text = full_info_text
            if img_path and img_path.startswith("http"):
                # "Link-Trick" für Web-Vorschau oben
                display_text = f"<a href='{img_path}'>&#8205;</a>" + full_info_text

            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=display_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=False 
            )
            set_context(user_id, {"model_key": key, "step": "waiting_for_prompt", "last_bot_msg_id": call.message.message_id})
        
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

    @bot.message_handler(content_types=['photo'])
    def on_image(msg):
        uid = msg.chat.id
        print(uid)
        ctx = get_context(uid)
        print(ctx)
        if not ctx or ctx.get("step") == "waiting_for_image": return
        
        file_info = bot.get_file(msg.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"temp/{uid}.jpg"
        if not os.path.exists("temp"): os.makedirs("temp")
        with open(path, "wb") as f: f.write(downloaded)
        
        ctx["image_path"] = path
        model_key = ctx.get("model_key")

        if model_key in MODELS_NO_PROMPT:
            run_generation(uid, model_key, "Upscale", path)
        elif model_key == "premium-headshot-pipeline":
            run_generation(uid, model_key, "", path)
        else:
            print("WAITING FOR PROMPT")
            ctx["step"] = "waiting_for_prompt"
            lang = get_lang(uid)
            msg = bot.send_message(uid, "✅ Bild da. Schreibe jetzt den Prompt:", reply_markup=keyboards.get_back_menu(lang, "nav_main"))
            ctx["last_bot_msg_id"] = msg.message_id
            set_context(uid, ctx)

    @bot.message_handler(func=lambda m: True)
    def on_prompt(msg):
        ctx = get_context(msg.chat.id)
        if ctx and ctx.get("step") == "waiting_for_prompt":
            process_prompt_logic(msg, ctx)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('prompt_'))
    def on_prompt_decision(call):
        uid = call.message.chat.id
        action = call.data.split('_')[1]
        data = pending_prompts.get(uid)
        if not data:
            try:
                bot.answer_callback_query(call.id, "Expired")
            except Exception:
                pass
            return

        if action == "accept":
            run_generation(uid, data['model_key'], data['optimized'], data['image_path'])
        elif action == "reject":
            run_generation(uid, data['model_key'], data['original'], data['image_path'])
        elif action == "edit":
            lang = get_lang(uid)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass