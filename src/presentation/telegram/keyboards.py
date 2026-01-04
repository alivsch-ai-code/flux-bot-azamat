from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from src.utils.strings import get_text

# --- 1. HAUPTMENÜ ---
def get_persistent_main_menu(lang="en"):    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(get_text("menu_image_studio", lang)), 
        KeyboardButton(get_text("menu_video_studio", lang)),
        KeyboardButton(get_text("menu_audio_studio", lang)), 
        KeyboardButton(get_text("menu_wallet", lang))
    )
    return markup

# --- 2. IMAGE STUDIO ---
def get_image_studio_menu(lang="en"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(get_text("menu_text2image", lang)),   
        KeyboardButton(get_text("menu_editimage", lang))       
    )
    markup.add(KeyboardButton(get_text("btn_back", lang)))
    return markup

# --- 3. MODELL-AUSWAHL: TEXT TO IMAGE ---
# Modell-Namen bleiben international gleich (Markennamen)
def get_text2img_models_menu(lang="en"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("💎 Flux 2 Pro"), KeyboardButton("💎 Imagen 4 Ultra"))
    markup.add(KeyboardButton("🚀 Flux 1.1 Pro"), KeyboardButton("✨ Imagen 4"))
    markup.add(KeyboardButton("⚡ Flux Schnell"), KeyboardButton("⚡ Imagen 4 Fast"))
    markup.add(KeyboardButton("🍌 Nano Banana Pro"), KeyboardButton("🎨 Ideogram v3"))
    markup.add(KeyboardButton(get_text("btn_back", lang)))
    return markup

# --- 4. MODELL-AUSWAHL: EDIT IMAGE ---
def get_editimg_models_menu(lang="en"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🤖 Gemini 2.5 Flash"),
        KeyboardButton("🛠️ Qwen Image Edit")
    )
    markup.add(KeyboardButton(get_text("btn_back", lang)))
    return markup

# --- 5. VIDEO STUDIO ---
def get_video_studio_menu(lang="en"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🎥 Sora 2"),
        KeyboardButton("🎞️ Wan 2.5"),
        KeyboardButton("📹 Veo 3.1")
    )
    markup.add(KeyboardButton(get_text("btn_back", lang)))
    return markup

# --- 6. AUDIO STUDIO ---
def get_audio_studio_menu(lang="en"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("🎵 Sonauto AI"))
    markup.add(KeyboardButton(get_text("btn_back", lang)))
    return markup