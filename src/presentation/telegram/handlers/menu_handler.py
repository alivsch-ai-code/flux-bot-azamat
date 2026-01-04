from telebot import TeleBot
from src.presentation.telegram import keyboards
from src.utils.strings import get_text

def get_user_lang(message):
    """Ermittelt 'de' oder 'en'."""
    user_lang = message.from_user.language_code
    if user_lang and user_lang[:2].lower() == "de":
        return "de"
    return "en"

def register(bot: TeleBot, generation_service, model_registry):

    # --- START COMMAND (Mit Transparenz-Nachricht) ---
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        lang = get_user_lang(message)
        
        # 1. Transparenz-Nachricht senden (HTML wichtig für Fettdruck)
        bot.send_message(
            message.chat.id,
            get_text("transparency_msg", lang),
            parse_mode='HTML'
        )

        # 2. Das Hauptmenü hinterherschicken
        bot.send_message(
            message.chat.id,
            get_text("welcome", lang),
            reply_markup=keyboards.get_persistent_main_menu(lang)
        )

    # --- GLOBALER BACK BUTTON ---
    # Hier zeigen wir NUR das Menü, ohne den langen Transparenz-Text noch mal zu posten.
    @bot.message_handler(func=lambda msg: msg.text in [get_text("btn_back", "en"), get_text("btn_back", "de")])
    def handle_back(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("welcome", lang), # Zurück zum Start-Text
            reply_markup=keyboards.get_persistent_main_menu(lang)
        )

    # --- NAV LEVEL 1 ---
    
    # Image Studio
    @bot.message_handler(func=lambda msg: msg.text in [get_text("menu_image_studio", "en"), get_text("menu_image_studio", "de")])
    def nav_image_studio(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("prompt_choose_mode", lang), 
            reply_markup=keyboards.get_image_studio_menu(lang)
        )

    # Video Studio
    @bot.message_handler(func=lambda msg: msg.text in [get_text("menu_video_studio", "en"), get_text("menu_video_studio", "de")])
    def nav_video_studio(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("prompt_choose_model", lang), 
            reply_markup=keyboards.get_video_studio_menu(lang)
        )

    # Audio Studio
    @bot.message_handler(func=lambda msg: msg.text in [get_text("menu_audio_studio", "en"), get_text("menu_audio_studio", "de")])
    def nav_audio_studio(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("prompt_choose_model", lang), 
            reply_markup=keyboards.get_audio_studio_menu(lang)
        )

    # --- NAV LEVEL 2 (Image Studio Submenus) ---

    # Text to Image
    @bot.message_handler(func=lambda msg: msg.text in [get_text("menu_text2image", "en"), get_text("menu_text2image", "de")])
    def nav_t2i_models(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("prompt_choose_model", lang), 
            reply_markup=keyboards.get_text2img_models_menu(lang)
        )

    # Edit Image
    @bot.message_handler(func=lambda msg: msg.text in [get_text("menu_editimage", "en"), get_text("menu_editimage", "de")])
    def nav_edit_models(message):
        lang = get_user_lang(message)
        bot.send_message(
            message.chat.id, 
            get_text("prompt_choose_model", lang), 
            reply_markup=keyboards.get_editimg_models_menu(lang)
        )