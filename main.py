import os
import telebot
import replicate
import threading
import requests
import json
from flask import Flask
from telebot import types
from io import BytesIO

# --- KONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- MODELLE & PREISE ---
MODELS = {
    "text": {
        "Llama 3 70B (Smart)": "meta/meta-llama-3-70b-instruct",
        "Llama 3 8B (Fast)": "meta/meta-llama-3-8b-instruct"
    },
    "code": {
        "Code Llama 70B": "meta/codellama-70b-instruct:a279116fe47a0f6570f496f9553698c1d27958561d56e9c017d74f20817c16c4",
    },
    "image": {
        "FLUX.1 Schnell (Turbo)": "black-forest-labs/flux-schnell",
        "Stable Diffusion XL": "stability-ai/sdxl:39ed52f2a78e934b3ba6e3a89f3325401994b91f4e24d435348658145025d57d",
    },
    "video": {
        # --- NEUE MODELLE ---
        "Wan 2.1 (Günstig & Gut)": "wan-video/wan-2.1-1.3b",
        "Kling 1.6 (Standard)": "kwaivgi/kling-v1.6-standard",
        
        # --- ALTE MODELLE (Auskommentiert) ---
        # "Google Veo 3.1 Fast": "google/veo-3.1-fast",
        # "Zeroscope (Alt)": "anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351"
    },
    "vision": { 
        "LLaVa 1.5": "yorickvp/llava-13b:b5f6212d032508382d61ff00469dd1d608d34f944985223c72b83445cd3c4314"
    },
    "edit": { 
        "InstructPix2Pix": "timothybrooks/instruct-pix2pix:30c1d0b916a6f8efce20493f5d61ee27491b63d3e9e0811e1976db17f804d6ce"
    },
    "faceswap": {
        "FaceSwap (InsightFace)": "lucataco/faceswap:9a4298548422074c3f57258c5d544497314ae4112df80d116f0d2109bd068e9c"
    }
}

# Preise in "Credits" (1000 Credits = 1 Euro ca.)
PRICES = {
    "text": 10,
    "code": 15,
    "image": 50,      # ca. 0,05 €
    "video": 400,     # ca. 0,40 € (Einkauf: ~0,20 $)
    "vision": 20,
    "edit": 40,
    "faceswap": 60
}

# --- STATE & DATABASE (Mock) ---
user_states = {}
user_credits = {} 
START_CREDITS = 1000

# --- HILFSFUNKTIONEN ---

def get_credits(user_id):
    if user_id not in user_credits:
        user_credits[user_id] = START_CREDITS
    return user_credits[user_id]

def check_balance(user_id, cost):
    return get_credits(user_id) >= cost

def deduct_credits(user_id, cost):
    user_credits[user_id] = get_credits(user_id) - cost
    return user_credits[user_id]

def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Text Chat", callback_data="menu_text"),
        types.InlineKeyboardButton("💻 Code", callback_data="menu_code"),
        types.InlineKeyboardButton("🎨 Bild", callback_data="menu_image"),
        types.InlineKeyboardButton("🎬 Video", callback_data="menu_video"),
        types.InlineKeyboardButton("👁️ Vision", callback_data="menu_vision"),
        types.InlineKeyboardButton("✏️ Edit", callback_data="menu_edit"),
        types.InlineKeyboardButton("🎭 Face Swap", callback_data="menu_faceswap"),
        types.InlineKeyboardButton("💰 Guthaben", callback_data="menu_balance")
    )
    return markup

def model_menu_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name, model_id in MODELS[category].items():
        # Trick: Wir nutzen den Namen als ID im Callback, um das 64-Byte Limit zu umgehen
        callback_str = f"set|{category}|{name}"
        markup.add(types.InlineKeyboardButton(f"{name} ({PRICES[category]} 💰)", callback_data=callback_str))
    markup.add(types.InlineKeyboardButton("🔙 Zurück", callback_data="menu_main"))
    return markup

# --- BOT LOGIK ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = {} 
    bot.send_message(
        user_id, 
        f"👋 <b>AI Bot Menü</b>\nGuthaben: {get_credits(user_id)} Credits", 
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )

# --- CALLBACK QUERY HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "menu_main":
        user_states[user_id] = {} 
        bot.edit_message_text("Hauptmenü:", user_id, call.message.message_id, reply_markup=main_menu_keyboard())

    elif data == "menu_balance":
        bot.answer_callback_query(call.id, f"Guthaben: {get_credits(user_id)} Credits", show_alert=True)

    elif data.startswith("menu_"):
        category = data.split("_")[1]
        bot.edit_message_text(f"Wähle ein Modell für {category.upper()}:", user_id, call.message.message_id, reply_markup=model_menu_keyboard(category))

    elif data.startswith("set|"):
        # Format: set|category|ModellName
        try:
            _, category, model_name = data.split("|")
            model_id = MODELS[category][model_name]
            
            user_states[user_id] = {
                "mode": category,
                "model_id": model_id,
                "model_name": model_name,
                "step": "waiting_for_input"
            }

            msg_text = f"✅ <b>Modell: {model_name}</b> ausgewählt.\n"
            if category == "faceswap":
                msg_text += "1️⃣ Bitte sende jetzt das <b>ZIEL-FOTO</b> (Körper)."
            elif category in ["vision", "edit"]:
                msg_text += "📸 Bitte sende jetzt ein <b>FOTO</b>."
            else:
                msg_text += "✍️ Bitte gib jetzt deinen <b>Prompt</b> ein:"
            
            bot.edit_message_text(msg_text, user_id, call.message.message_id, parse_mode="HTML")
        except Exception as e:
            bot.answer_callback_query(call.id, "Fehler bei Auswahl")
            print(e)

# --- TEXT INPUT HANDLER ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if not state or state.get("step") != "waiting_for_input":
        bot.reply_to(message, "Bitte wähle erst eine Funktion im Menü: /start")
        return

    mode = state["mode"]
    cost = PRICES[mode]

    if not check_balance(user_id, cost):
        bot.reply_to(message, f"❌ Nicht genug Credits! Du brauchst {cost}, hast aber nur {get_credits(user_id)}.")
        return

    # A. Text & Code
    if mode in ["text", "code"]:
        processing_msg = bot.reply_to(message, "🤔 ...")
        try:
            output = replicate.run(state["model_id"], input={"prompt": message.text, "max_tokens": 1024})
            full_response = "".join(output)
            bot.reply_to(message, full_response)
            deduct_credits(user_id, cost)
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")
        finally:
            bot.delete_message(user_id, processing_msg.message_id)

    # B. Bild & Video
    elif mode in ["image", "video"]:
        status_text = "🎨 Male Bild..." if mode == "image" else "🎬 Drehe Video (ca. 1-2 Min)..."
        processing_msg = bot.reply_to(message, status_text)
        bot.send_chat_action(user_id, 'upload_video' if mode == 'video' else 'upload_photo')
        
        try:
            # Inputs anpassen
            inputs = {"prompt": message.text}
            if mode == "image": 
                inputs["aspect_ratio"] = "1:1"
                inputs["output_format"] = "jpg"
            
            # API Call
            output = replicate.run(state["model_id"], input=inputs)
            media_url = output[0] if isinstance(output, list) else output
            
            if mode == "image":
                bot.send_photo(user_id, media_url, caption=f"✨ {message.text}")
            else:
                bot.send_video(user_id, media_url, caption=f"🎬 {message.text}")
            
            rest = deduct_credits(user_id, cost)
            bot.send_message(user_id, f"💰 Guthaben: {rest} Credits")
            
        except Exception as e:
            bot.reply_to(message, f"❌ Fehler: {e}")
        finally:
            bot.delete_message(user_id, processing_msg.message_id)
            
    # C. Edit Mode (Schritt 2)
    elif mode == "edit" and state.get("step") == "waiting_for_edit_prompt":
        image_url = state["temp_image_url"]
        prompt = message.text
        processing_msg = bot.reply_to(message, "✏️ Bearbeite...")
        try:
            output = replicate.run(state["model_id"], input={"image": image_url, "prompt": prompt})
            bot.send_photo(user_id, output[0], caption=f"✨ {prompt}")
            deduct_credits(user_id, cost)
            user_states[user_id] = {} 
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")

# --- FOTO INPUT HANDLER ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if not state:
        bot.reply_to(message, "Bitte wähle erst eine Funktion: /start")
        return

    mode = state["mode"]
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
    
    if mode == "vision":
        bot.reply_to(message, "👁️ Analysiere...")
        try:
            output = replicate.run(state["model_id"], input={"image": file_url, "prompt": "Describe this image."})
            full_response = "".join(output)
            bot.reply_to(message, full_response)
            deduct_credits(user_id, PRICES["vision"])
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")

    elif mode == "edit":
        state["temp_image_url"] = file_url
        state["step"] = "waiting_for_edit_prompt"
        bot.reply_to(message, "📸 Bild da! Was soll ich ändern? (z.B. 'Make it winter')")

    elif mode == "faceswap":
        if state["step"] == "waiting_for_input":
            state["target_image_url"] = file_url
            state["step"] = "waiting_for_source_face"
            bot.reply_to(message, "1️⃣ Ziel gespeichert.\n2️⃣ Sende jetzt das <b>GESICHT</b>.", parse_mode="HTML")
        
        elif state["step"] == "waiting_for_source_face":
            bot.reply_to(message, "🎭 Tausche Gesichter...")
            try:
                output = replicate.run(
                    state["model_id"],
                    input={"swap_image": file_url, "target_image": state["target_image_url"]}
                )
                bot.send_photo(user_id, output, caption="🎭 Resultat")
                deduct_credits(user_id, PRICES["faceswap"])
                user_states[user_id] = {} 
            except Exception as e:
                bot.reply_to(message, f"Fehler: {e}")

# --- SERVER ---
@app.route('/')
def home():
    return "🤖 ULTRA BOT ONLINE"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)