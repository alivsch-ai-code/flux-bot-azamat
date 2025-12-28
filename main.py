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

# --- MODELLE & PREISE (Config) ---
MODELS = {
    "text": {
        "Llama 3 70B (Smart)": "meta/meta-llama-3-70b-instruct",
        "Llama 3 8B (Fast)": "meta/meta-llama-3-8b-instruct"
    },
    "code": {
        "Code Llama 70B": "meta/codellama-70b-instruct:a279116fe47a0f6570f496f9553698c1d27958561d56e9c017d74f20817c16c4",
        "DeepSeek Coder": "deepseek-ai/deepseek-coder-33b-instruct" # Beispiel, falls auf Replicate verfügbar
    },
    "image": {
        "FLUX.1 Schnell (Turbo)": "black-forest-labs/flux-schnell",
        "Stable Diffusion XL": "stability-ai/sdxl:39ed52f2a78e934b3ba6e3a89f3325401994b91f4e24d435348658145025d57d",
        "Playground v2.5": "playgroundai/playground-v2.5-1024px-aesthetic:a45f82a1382bed5c7aeb861dac7c7d1919428cf3954f9084657a1b38cd6888db"
    },
    "video": {
        "Google Veo 3.1 Fast": "google/veo-3.1-fast",
        "Zeroscope (Günstig)": "anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351"
    },
    "vision": { # Bildbeschreibung
        "LLaVa 1.5": "yorickvp/llava-13b:b5f6212d032508382d61ff00469dd1d608d34f944985223c72b83445cd3c4314"
    },
    "edit": { # Bild verändern
        "InstructPix2Pix": "timothybrooks/instruct-pix2pix:30c1d0b916a6f8efce20493f5d61ee27491b63d3e9e0811e1976db17f804d6ce"
    },
    "faceswap": {
        "FaceSwap (InsightFace)": "lucataco/faceswap:9a4298548422074c3f57258c5d544497314ae4112df80d116f0d2109bd068e9c"
    }
}

# Preise in "Credits"
PRICES = {
    "text": 10,
    "code": 15,
    "image": 50,
    "video": 500,
    "vision": 20,
    "edit": 40,
    "faceswap": 60
}

# --- STATE MANAGEMENT ---
# Hier speichern wir temporär, was der User gerade tut
# Struktur: { user_id: { "state": "waiting_for_prompt", "model": "...", "mode": "image", "temp_image": data } }
user_states = {}

# Demo-Datenbank für Credits (Reset bei Neustart!)
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
        types.InlineKeyboardButton("💻 Code Generieren", callback_data="menu_code"),
        types.InlineKeyboardButton("🎨 Bild Generieren", callback_data="menu_image"),
        types.InlineKeyboardButton("🎬 Video Generieren", callback_data="menu_video"),
        types.InlineKeyboardButton("👁️ Bild Beschreiben", callback_data="menu_vision"),
        types.InlineKeyboardButton("✏️ Bild Bearbeiten", callback_data="menu_edit"),
        types.InlineKeyboardButton("🎭 Face Swap", callback_data="menu_faceswap"),
        types.InlineKeyboardButton("💰 Mein Guthaben", callback_data="menu_balance")
    )
    return markup

def model_menu_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name, model_id in MODELS[category].items():
        # Wir übergeben Kategorie UND Modell-ID im Callback
        # Achtung: Callback Data hat ein 64 Byte Limit bei Telegram! Wir müssen tricksen oder kurze IDs nutzen.
        # Hier nutzen wir den Key aus dem Dict, um es kurz zu halten.
        callback_str = f"setmodel|{category}|{name}"
        markup.add(types.InlineKeyboardButton(f"{name} ({PRICES[category]} 💰)", callback_data=callback_str))
    markup.add(types.InlineKeyboardButton("🔙 Zurück", callback_data="menu_main"))
    return markup

# --- BOT LOGIK ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = {} # Reset State
    bot.send_message(
        user_id, 
        f"👋 Willkommen im AI-Multi-Tool Bot!\nDu hast {get_credits(user_id)} Credits.\nWähle eine Funktion:", 
        reply_markup=main_menu_keyboard()
    )

# --- CALLBACK QUERY HANDLER (Menü Klicks) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "menu_main":
        user_states[user_id] = {} # Reset
        bot.edit_message_text("Hauptmenü:", user_id, call.message.message_id, reply_markup=main_menu_keyboard())

    elif data == "menu_balance":
        bot.answer_callback_query(call.id, f"Dein Guthaben: {get_credits(user_id)} Coins")

    elif data.startswith("menu_"):
        # User hat eine Kategorie gewählt (z.B. menu_image)
        category = data.split("_")[1]
        bot.edit_message_text(f"Wähle ein Modell für {category.upper()}:", user_id, call.message.message_id, reply_markup=model_menu_keyboard(category))

    elif data.startswith("setmodel|"):
        # User hat ein Modell ausgewählt
        _, category, model_name = data.split("|")
        model_id = MODELS[category][model_name]
        
        # State speichern
        user_states[user_id] = {
            "mode": category,
            "model_id": model_id,
            "model_name": model_name,
            "step": "waiting_for_input"
        }

        # Anweisungen je nach Modus
        if category in ["text", "code", "image", "video"]:
            bot.send_message(user_id, f"✅ Modell: {model_name}\n✍️ Bitte gib jetzt deinen Prompt ein:")
        elif category == "vision":
            bot.send_message(user_id, f"✅ Modell: {model_name}\n📸 Bitte sende jetzt ein FOTO, das ich beschreiben soll.")
        elif category == "edit":
            bot.send_message(user_id, f"✅ Modell: {model_name}\n📸 Bitte sende das FOTO, das du bearbeiten willst.")
        elif category == "faceswap":
            bot.send_message(user_id, f"✅ Modell: {model_name}\n1️⃣ Bitte sende zuerst das ZIEL-FOTO (Körper/Hintergrund).")

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
        bot.reply_to(message, "❌ Nicht genug Credits! /start")
        return

    # A. Text & Code Generierung
    if mode in ["text", "code"]:
        processing_msg = bot.reply_to(message, "🤔 Denke nach...")
        try:
            output = replicate.run(state["model_id"], input={"prompt": message.text, "max_tokens": 512})
            # Llama gibt oft eine Liste oder einen Generator zurück, wir müssen es zusammenbauen
            full_response = "".join(output)
            bot.reply_to(message, full_response)
            deduct_credits(user_id, cost)
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")
        finally:
            bot.delete_message(user_id, processing_msg.message_id)

    # B. Bild & Video Generierung (Prompt Verarbeitung)
    elif mode in ["image", "video"]:
        processing_msg = bot.reply_to(message, "🎨 Generiere Medien... (kann dauern)")
        try:
            # Replicate Input Parameter variieren je nach Modell leicht
            inputs = {"prompt": message.text}
            if mode == "image": inputs["aspect_ratio"] = "1:1" # Standard für Flux
            
            output = replicate.run(state["model_id"], input=inputs)
            
            # Ausgabe verarbeiten
            media_url = output[0] if isinstance(output, list) else output
            
            if mode == "image":
                bot.send_photo(user_id, media_url, caption=f"✨ {message.text}")
            else:
                bot.send_video(user_id, media_url, caption=f"🎬 {message.text}")
            
            deduct_credits(user_id, cost)
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")
        finally:
            bot.delete_message(user_id, processing_msg.message_id)
            
    # C. Edit Mode (Schritt 2: Prompt nach Bild)
    elif mode == "edit" and state.get("step") == "waiting_for_edit_prompt":
        # Wir haben das Bild schon im State, jetzt kommt der Prompt
        image_url = state["temp_image_url"] # URL vom Telegram Server
        prompt = message.text
        
        processing_msg = bot.reply_to(message, "✏️ Bearbeite Bild...")
        try:
            output = replicate.run(
                state["model_id"],
                input={"image": image_url, "prompt": prompt}
            )
            bot.send_photo(user_id, output[0], caption=f"✨ {prompt}")
            deduct_credits(user_id, cost)
            user_states[user_id] = {} # Reset
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
    
    # Datei-Info von Telegram holen
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
    
    # A. Vision (Bild beschreiben)
    if mode == "vision":
        bot.reply_to(message, "👁️ Analysiere Bild...")
        try:
            output = replicate.run(
                state["model_id"],
                input={"image": file_url, "prompt": "Describe this image in detail."}
            )
            full_response = "".join(output)
            bot.reply_to(message, full_response)
            deduct_credits(user_id, PRICES["vision"])
        except Exception as e:
            bot.reply_to(message, f"Fehler: {e}")

    # B. Edit (Bild bearbeiten - Schritt 1)
    elif mode == "edit":
        # Bild URL speichern, jetzt nach Prompt fragen
        state["temp_image_url"] = file_url
        state["step"] = "waiting_for_edit_prompt"
        bot.reply_to(message, "📸 Bild erhalten! Was soll ich ändern? (z.B. 'Make it look like a painting' oder 'Turn the cat into a dog')")

    # C. Face Swap (Schritt 1 & 2)
    elif mode == "faceswap":
        if state["step"] == "waiting_for_input":
            # Das war Bild 1 (Target)
            state["target_image_url"] = file_url
            state["step"] = "waiting_for_source_face"
            bot.reply_to(message, "1️⃣ Zielbild gespeichert.\n2️⃣ Sende jetzt das Foto mit dem GESICHT, das wir einfügen sollen.")
        
        elif state["step"] == "waiting_for_source_face":
            # Das war Bild 2 (Source)
            source_url = file_url
            target_url = state["target_image_url"]
            
            bot.reply_to(message, "🎭 Tausche Gesichter (InsightFace)...")
            try:
                output = replicate.run(
                    state["model_id"],
                    input={"swap_image": source_url, "target_image": target_url}
                )
                bot.send_photo(user_id, output, caption="🎭 Face Swap Result")
                deduct_credits(user_id, PRICES["faceswap"])
                user_states[user_id] = {} # Reset
            except Exception as e:
                bot.reply_to(message, f"Fehler: {e}")

# --- SERVER KEEP-ALIVE ---
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