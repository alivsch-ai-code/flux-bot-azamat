from telebot import TeleBot
from src.utils.strings import get_text
from src.presentation.telegram import keyboards

# Helper, um Sprache zu holen (Code Duplikation vermeiden wir hier simpel durch erneute Definition oder Import)
def get_user_lang(message):
    user_lang = message.from_user.language_code
    if user_lang and user_lang[:2].lower() == "de":
        return "de"
    return "en"

def register(bot: TeleBot, generation_service, model_registry: dict):

    # Mapping: Button Text -> Config Key
    MODEL_MAPPING = {
        "💎 Flux 2 Pro": "flux-2-pro",
        "🚀 Flux 1.1 Pro": "flux-1.1-pro",
        "⚡ Flux Schnell": "flux-schnell",
        "💎 Imagen 4 Ultra": "imagen-4-ultra",
        "✨ Imagen 4": "imagen-4",
        "⚡ Imagen 4 Fast": "imagen-4-fast",
        "🎨 Ideogram v3": "ideogram-v3",
        "🍌 Nano Banana Pro": "nano-banana-pro",
        "🤖 Gemini 2.5 Flash": "gemini-2.5",
        "🛠️ Qwen Image Edit": "qwen-image",
        "🎥 Sora 2": "sora-2",
        "🎞️ Wan 2.5": "wan-2.5",
        "📹 Veo 3.1": "veo-3.1",
        "🎵 Sonauto AI": "sonauto"
    }
    
    KNOWN_BUTTONS = list(MODEL_MAPPING.keys())

    # --- SCHRITT A: Modell Auswahl ---
    @bot.message_handler(func=lambda msg: msg.text in KNOWN_BUTTONS)
    def handle_model_selection(message):
        lang = get_user_lang(message)
        model_name = message.text
        user_id = message.chat.id
        
        internal_key = MODEL_MAPPING.get(model_name)
        model = model_registry.get(internal_key)
        
        if not model:
            bot.send_message(user_id, "❌ Error: Model config missing.")
            return

        price_euro = model.cost / 100
        
        # Text aus strings.py formatieren
        info_text = get_text("msg_selected", lang).format(
            model=model_name, 
            price=f"{price_euro:.2f}"
        )
        
        msg = bot.send_message(
            user_id, 
            info_text,
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            msg, handle_prompt_input, bot, generation_service, model_registry, internal_key
        )

    # --- SCHRITT B: Generierung ---
    def handle_prompt_input(message, bot, service, registry, model_key):
        lang = get_user_lang(message)
        user_id = message.chat.id
        prompt = message.text

        # Abbruch Check (Multilingual)
        back_btns = [get_text("btn_back", "en"), get_text("btn_back", "de")]
        if prompt in KNOWN_BUTTONS or prompt in back_btns:
            bot.send_message(user_id, get_text("err_aborted", lang))
            return

        if not prompt:
            bot.send_message(user_id, get_text("err_no_text", lang))
            return

        # Status Nachricht
        status_text = get_text("msg_generating", lang).format(model=model_key)
        status_msg = bot.send_message(user_id, status_text)
        
        model = registry.get(model_key)
        
        success, result = service.process_request(user_id, model, prompt)
        
        if success:
            if model.type == "video":
                 bot.send_video(user_id, result, caption=f"🎬 {prompt}")
            elif model.type == "audio":
                 bot.send_audio(user_id, result, caption=f"🎵 {prompt}")
            else:
                 bot.send_photo(user_id, result, caption=f"✨ {prompt}")
            
            bot.delete_message(user_id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ Error: {result}", user_id, status_msg.message_id)