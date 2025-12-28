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

# --- MODELLE ---
# Hinweis: "Imagen 4" gibt es noch nicht public, wir nutzen Imagen 3 (SOTA).
# "Nano Banana" ist der Codename für Imagen 3 Fast.
MODELS = {
    "text": {
        "Llama 3 70B": "meta/meta-llama-3-70b-instruct",
    },
    "code": {
        "Code Llama 70B": "meta/codellama-70b-instruct:a279116fe47a0f6570f496f9553698c1d27958561d56e9c017d74f20817c16c4",
    },
    "image": {
        # --- PREIS: 4 Cent (~40 Coins) ---
        "Google Imagen 3 (High Qual.)": "google/imagen-3",
        
        # --- PREIS: 3,9 Cent (~39 Coins) ---
        "Google Imagen 3 Fast (Banana)": "google/imagen-3-fast",
        
        # --- PREIS: 3 Cent (~30 Coins) ---
        "Ideogram v2 Turbo (Text-Pro)": "ideogram-ai/ideogram-v2-turbo",
        
        # Standard
        "FLUX.1 Schnell": "black-forest-labs/flux-schnell",
    },
    "video": {
        "Wan 2.5 Fast (480p)": "wan-video/wan-2.5-t2v-fast",
        "Kling 1.6 Standard": "kwaivgi/kling-v1.6-standard",
    },
    "vision": { 
        "LLaVa 1.5": "yorickvp/llava-13b:b5f6212d032508382d61ff00469dd1d608d34f944985223c72b83445cd3c4314"
    },
    "edit": { 
        # Inpainting / Fill
        "FLUX Fill (Pro)": "black-forest-labs/flux-fill-dev", # Dev ist oft günstiger/schneller verfügbar
        "Qwen Edit": "ali-vilab/inpaint-anything", # Alternativ Qwen VL, falls spezifische ID bekannt. Nutze hier Standard Inpaint als Fallback.
    },
    "faceswap": {
        # Klassisch: Foto gegen Foto
        "Classic (InsightFace)": "lucataco/faceswap:9a4298548422074c3f57258c5d544497314ae4112df80d116f0d2109bd068e9c",
        
        # Neu: Gesicht + Prompt
        "Ideogram Swap (Gesicht+Text)": "fofr/face-swap-with-ideogram" 
    }
}

# Preise in "Credits" (10 Cent = 100 Credits)
PRICES = {
    "text": 10,
    "code": 15,
    "vision": 20,
    
    # Image
    "google_img": 40,   # 4 Cent
    "google_fast": 39,  # 3.9 Cent
    "ideogram": 30,     # 3 Cent
    "flux": 20,         # Günstig
    
    # Video
    "video": 400,
    
    # Edit
    "edit": 40,
    
    # Faceswap
    "faceswap_classic": 50,
    "faceswap_ideo": 110 # 11 Cent
}

# --- STATE & DATABASE ---
user_states = {}
user_credits = {} 
START_CREDITS = 2000 # Etwas mehr Startguthaben zum Testen

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

def get_price_for_model(category, model_name):
    """Ermittelt den Preis basierend auf dem Modellnamen"""
    if category == "image":
        if "Imagen 3 Fast" in model_name: return PRICES["google_fast"]
        if "Imagen 3" in model_name: return PRICES["google_img"]
        if "Ideogram" in model_name: return PRICES["ideogram"]
        return PRICES["flux"]
    
    if category == "faceswap":
        if "Ideogram" in model_name: return PRICES["faceswap_ideo"]
        return PRICES["faceswap_classic"]
        
    return PRICES.get(category, 50) # Fallback

def create_model_info_text():
    """Erstellt den Info-Text für /start"""
    txt = "🤖 <b>Verfügbare Modelle & Preise:</b>\n\n"
    
    txt += "🎨 <b>BILD (Empfehlung: Imagen 3):</b>\n"
    for m in MODELS["image"]:
        p = get_price_for_model("image", m)
        txt += f"- {m}: {p} Coins\n"
        
    txt += "\n🎬 <b>VIDEO (Empfehlung: Wan 2.5):</b>\n"
    for m in MODELS["video"]:
        txt += f"- {m}: {PRICES['video']} Coins\n"
        
    txt += "\n🎭 <b>FACE SWAP:</b>\n"
    txt += f"- Classic: {PRICES['faceswap_classic']} Coins\n"
    txt += f"- Mit Ideogram (Prompt): {PRICES['faceswap_ideo']} Coins\n"
    
    txt += "\n💡 <i>Tipp: Nutze 'Ideogram' für Text im Bild!</i>"
    return txt

def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Text", callback_data="menu_text"),
        types.InlineKeyboardButton("🎨 Bild", callback_data="menu_image"),
        types.InlineKeyboardButton("🎬 Video", callback_data="menu_video"),
        types.InlineKeyboardButton("✏️ Bild ändern", callback_data="menu_edit"),
        types.InlineKeyboardButton("🎭 Face Swap", callback_data="menu_faceswap"),
        types.InlineKeyboardButton("💰 Guthaben", callback_data="menu_balance")
    )
    return markup

def model_menu_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name, model_id in MODELS[category].items():
        price = get_price_for_model(category, name)
        callback_str = f"set|{category}|{name}"
        markup.add(types.InlineKeyboardButton(f"{name} ({price} 💰)", callback_data=callback_str))
    markup.add(types.InlineKeyboardButton("🔙 Zurück", callback_data="menu_main"))
    return markup

# --- BOT LOGIK ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = {} 
    
    info_text = f"👋 <b>Willkommen!</b>\n\n{create_model_info_text()}\n\n"
    info_text += f"Dein Guthaben: <b>{get_credits(user_id)} Credits</b>"
    
    bot.send_message(user_id, info_text, parse_mode="HTML", reply_markup=main_menu_keyboard())

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "menu_main":
        user_states[user_id] = {}
        bot.edit_message_text("Hauptmenü:", user_id, call.message.message_id, reply_markup=main_menu_keyboard())

    elif data == "menu_balance":
        bot.answer_callback_query(call.id, f"Stand: {get_credits(user_id)} Credits", show_alert=True)

    elif data.startswith("menu_"):
        category = data.split("_")[1]
        bot.edit_message_text(f"Wähle ein Modell für {category.upper()}:", user_id, call.message.message_id, reply_markup=model_menu_keyboard(category))

    elif data.startswith("set|"):
        try:
            _, category, model_name = data.split("|")
            model_id = MODELS[category][model_name]
            
            # State setzen
            user_states[user_id] = {
                "mode": category,
                "model_id": model_id,
                "model_name": model_name,
                "step": "waiting_for_input_1" # Start-Schritt
            }

            msg = f"✅ <b>{model_name}</b> ausgewählt.\n"
            
            # Anweisungen je nach Modell-Typ
            if category == "faceswap":
                if "Ideogram" in model_name:
                    msg += "1️⃣ Sende jetzt das Foto mit dem <b>GESICHT</b> (Selfie)."
                else:
                    msg += "1️⃣ Sende jetzt das <b>ZIEL-FOTO</b> (Körper/Hintergrund)."
            elif category == "edit":
                msg += "📸 Sende jetzt das <b>FOTO</b>, das du bearbeiten willst."
            elif category == "image" or category == "video":
                msg += "✍️ Gib deinen <b>Prompt</b> ein:"
            elif category == "text":
                msg += "✍️ Schreib deine Frage:"
            
            bot.edit_message_text(msg, user_id, call.message.message_id, parse_mode="HTML")
            
        except Exception as e:
            print(e)
            bot.answer_callback_query(call.id, "Fehler.")

# --- HANDLER FÜR FOTOS ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if not state:
        bot.reply_to(message, "Bitte wähle erst eine Funktion: /start")
        return

    mode = state["mode"]
    model_name = state["model_name"]
    step = state.get("step")
    
    # Datei URL holen
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

    # --- LOGIK FÜR EDIT (Bild verändern) ---
    if mode == "edit" and step == "waiting_for_input_1":
        state["image_url"] = file_url
        state["step"] = "waiting_for_edit_prompt" # Nächster Schritt: Text
        bot.reply_to(message, "✅ Bild empfangen!\n✍️ Schreib jetzt, was ich ändern soll (z.B. 'Füge eine Brille hinzu' oder 'Mache es zu Nacht').")
        return

    # --- LOGIK FÜR FACESWAP (Classic) ---
    if mode == "faceswap" and "Classic" in model_name:
        if step == "waiting_for_input_1":
            state["target_url"] = file_url
            state["step"] = "waiting_for_face_photo"
            bot.reply_to(message, "✅ Zielbild gespeichert.\n2️⃣ Sende jetzt das Foto mit dem <b>GESICHT</b>, das eingefügt werden soll.", parse_mode="HTML")
        elif step == "waiting_for_face_photo":
            # Start Generierung
            start_generation(message, state, swap_image=file_url)

    # --- LOGIK FÜR FACESWAP (Ideogram) ---
    if mode == "faceswap" and "Ideogram" in model_name:
        if step == "waiting_for_input_1":
            state["face_url"] = file_url
            state["step"] = "waiting_for_prompt"
            bot.reply_to(message, "✅ Gesicht gespeichert.\n✍️ Beschreibe jetzt das Bild, das ich generieren soll (z.B. 'A superhero flying in space').")

# --- HANDLER FÜR TEXT ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if not state:
        bot.reply_to(message, "Bitte Menü nutzen: /start")
        return

    mode = state["mode"]
    model_name = state["model_name"]
    step = state.get("step")
    cost = get_price_for_model(mode, model_name)

    # 1. Geld Check
    if not check_balance(user_id, cost):
        bot.reply_to(message, f"❌ Zu wenig Credits ({get_credits(user_id)}). Benötigt: {cost}.")
        return

    # --- INPUT: EDIT PROMPT ---
    if mode == "edit" and step == "waiting_for_edit_prompt":
        start_generation(message, state, prompt=message.text)

    # --- INPUT: FACESWAP IDEOGRAM PROMPT ---
    elif mode == "faceswap" and "Ideogram" in model_name and step == "waiting_for_prompt":
        start_generation(message, state, prompt=message.text)

    # --- INPUT: NORMALE GENERIERUNG (Bild/Video/Text) ---
    elif step == "waiting_for_input_1" and mode in ["image", "video", "text"]:
        start_generation(message, state, prompt=message.text)
        
    else:
        bot.reply_to(message, "❌ Unerwartete Eingabe. Bitte starte neu mit /start")

# --- ZENTRALE GENERIERUNGS-FUNKTION ---
def start_generation(message, state, prompt=None, swap_image=None):
    user_id = message.chat.id
    mode = state["mode"]
    model_id = state["model_id"]
    model_name = state["model_name"]
    cost = get_price_for_model(mode, model_name)
    
    status_msg = bot.reply_to(message, f"⏳ Arbeite mit {model_name}...")
    
    try:
        output = None
        inputs = {}
        
        # --- PARAMETER SETZEN ---
        if mode == "image":
            inputs["prompt"] = prompt
            if "Ideogram" in model_name:
                inputs["aspect_ratio"] = "1:1"
            elif "Imagen" in model_name:
                inputs["aspect_ratio"] = "1:1"
        
        elif mode == "video":
            inputs["prompt"] = prompt
            inputs["size"] = "832*480" # Sparmodus für Wan
            inputs["duration"] = 5
            
        elif mode == "edit":
            inputs["image"] = state["image_url"]
            inputs["prompt"] = prompt
            # FLUX Fill braucht oft "mask" oder "image" - Standard Prompt Edit nutzt image+prompt
            if "FLUX" in model_name:
                inputs["mask_image"] = None # Auto-Masking falls unterstützt, sonst einfaches Edit
            
        elif mode == "faceswap":
            if "Classic" in model_name:
                inputs["target_image"] = state["target_url"]
                inputs["swap_image"] = swap_image
            elif "Ideogram" in model_name:
                inputs["test_image"] = state["face_url"] # Gesicht
                inputs["prompt"] = prompt # Text
        
        elif mode == "text":
            inputs["prompt"] = prompt
            inputs["max_tokens"] = 1000

        # --- API AUFRUF ---
        output = replicate.run(model_id, input=inputs)
        
        # --- ERGEBNIS SENDEN ---
        if mode == "text":
            full_text = "".join(output)
            bot.reply_to(message, full_text)
        else:
            media_url = output[0] if isinstance(output, list) else output
            
            caption = f"✨ {prompt[:50]}..." if prompt else "✨ Ergebnis"
            caption += f"\n💰 Rest: {deduct_credits(user_id, cost)} Credits"
            
            if mode == "video":
                bot.send_video(user_id, media_url, caption=caption)
            else:
                bot.send_photo(user_id, media_url, caption=caption)
        
        # State Reset
        user_states[user_id] = {}
        bot.delete_message(user_id, status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Fehler bei Replicate: {str(e)}")
        print(f"Error: {e}")

# --- SERVER ---
@app.route('/')
def home():
    return "🤖 ULTRA BOT V2 ONLINE"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)