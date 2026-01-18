from telebot import types
from src.utils.strings import get_text
from urllib.parse import quote

def btn(text, callback_data):
    return types.InlineKeyboardButton(text=text, callback_data=callback_data)

def get_main_menu_inline(lang: str = "de"):
    markup = types.InlineKeyboardMarkup(row_width=2)

    # 1. Profil
    markup.add(btn(get_text("menu_profile", lang), "nav_profile"))

    # 2. Hauptfunktionen
    markup.add(
        btn(get_text("menu_image_studio", lang), "nav_image"),
        btn(get_text("menu_video_studio", lang), "nav_video")
    )
    
    # 3. Audio & Tools
    markup.add(
        btn(get_text("menu_audio_studio", lang), "nav_audio"),
        btn(get_text("menu_tools_edit", lang), "nav_tools")
    )

    # 4. Settings & Shop
    markup.add(
        btn(get_text("menu_settings", lang), "nav_settings"), # Settings Button
        btn(get_text("menu_shop", lang), "cmd_shop")
    )
    
    # 5. Support
    markup.add(btn(get_text("menu_support", lang), "nav_support"))

    return markup

# --- NEU: AUDIO STUDIO MENÜ (wie im Screenshot) ---
def get_audio_studio_menu(lang: str = "de"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Buttons genau wie im Bild
    markup.add(
        btn(get_text("btn_tts", lang), "sel_tts"),           # Sprachsynthese
        btn(get_text("btn_clone", lang), "sel_voice-clone")  # Stimmklonung
    )
    markup.add(
        btn(get_text("btn_suno", lang), "sel_suno"),         # SUNO
        btn(get_text("btn_vid2aud", lang), "sel_vid2audio")  # Video zu Audio
    )
    markup.add(
        btn(get_text("btn_sound", lang), "sel_sound-gen"),   # Sound-Gen
        btn(get_text("btn_transcribe", lang), "sel_audio2text") # Audio zu Text
    )
    
    markup.add(btn(get_text("btn_back", lang), "nav_main"))
    return markup

def get_settings_menu(settings: dict, lang: str = "de"):
    """Erstellt das Einstellungs-Menü mit Toggles."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Sprache wählen
    lang_label = lang.upper()
    if lang == "de": lang_label = "🇩🇪 Deutsch"
    elif lang == "en": lang_label = "🇬🇧 English"
    elif lang == "ru": lang_label = "🇷🇺 Русский"
    elif lang == "kk": lang_label = "🇰🇿 Қазақша"
    
    markup.add(btn(get_text("btn_lang", lang).format(lang=lang_label), "nav_lang"))
    
    # Auto-Optimierung Toggle
    if settings.get("auto_opt", True):
        markup.add(btn(get_text("btn_opt_on", lang), "toggle_opt"))
    else:
        markup.add(btn(get_text("btn_opt_off", lang), "toggle_opt"))
        
    # NEU: Daily News Toggle
    if settings.get("daily_msg", True):
        markup.add(btn(get_text("btn_daily_on", lang), "toggle_daily"))
    else:
        markup.add(btn(get_text("btn_daily_off", lang), "toggle_daily"))
        
    # Free Credits (jetzt hier als Extra)
    markup.add(btn(get_text("menu_referral", lang), "nav_referral"))

    markup.add(btn(get_text("btn_back", lang), "nav_main"))
    return markup

def get_language_menu(lang: str = "de"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("🇩🇪 Deutsch", "set_lang_de"),
        btn("🇬🇧 English", "set_lang_en"),
        btn("🇷🇺 Русский", "set_lang_ru"),
        btn("🇰🇿 Қазақша", "set_lang_kk")
    )
    markup.add(btn(get_text("btn_back", lang), "nav_settings"))
    return markup

def _create_model_menu_inline(model_registry: dict, filter_types: list, lang: str, row_width=2, back_target="nav_main"):
    markup = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = []
    for key, model in model_registry.items():
        if any(t in model.type for t in filter_types):
            if "pipeline" in model.type and len(filter_types) == 1 and "image" in filter_types: continue 
            buttons.append(btn(f"{model.name} ({model.cost} ⭐️)", f"sel_{key}"))
    markup.add(*buttons)
    markup.add(btn(get_text("btn_back", lang), back_target))
    return markup

def get_image_studio_menu(model_registry: dict, lang: str = "de"):
    return _create_model_menu_inline(model_registry, ["image","text-to-image","image-to-image"], lang, 2, "nav_main")

def get_video_studio_menu(model_registry: dict, lang: str = "de"):
    return _create_model_menu_inline(model_registry, ["video"], lang, 1, "nav_main")

def get_edit_menu(model_registry: dict, lang: str = "de"):
    return _create_model_menu_inline(model_registry, ["edit", "upscale", "analysis"], lang, 2, "nav_main")

def get_share_menu(ref_link: str, share_text: str, lang: str = "de"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    url_tg = f"https://t.me/share/url?url={quote(ref_link)}&text={quote(share_text)}"
    url_vk = f"https://vk.com/share.php?url={quote(ref_link)}&title={quote(share_text)}"
    markup.add(
        types.InlineKeyboardButton(get_text("btn_share_tg", lang), url=url_tg),
        types.InlineKeyboardButton(get_text("btn_share_vk", lang), url=url_vk)
    )
    markup.add(btn(get_text("btn_back", lang), "nav_settings"))
    return markup

def get_back_menu(lang: str = "de", target="nav_main"):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(get_text("btn_back", lang), target))
    return markup