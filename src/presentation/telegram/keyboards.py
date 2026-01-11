# keyboards.py
from telebot import types
from src.utils.strings import get_text
from urllib.parse import quote

def get_persistent_main_menu(model_registry: dict, lang: str = "de"):
    """
    Erstellt das Hauptmenü dynamisch basierend auf den geladenen Modellen und der Sprache.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # 1. SPECIAL BUTTON: Pro Bewerbungsfoto
    # Wir holen den Basistext (z.B. "Pro Bewerbungsfoto" oder "Pro Headshot")
    base_text = get_text("btn_pro_headshot", lang) 
    special_btn_text = f"{base_text} (?? ⭐️)" # Fallback
    
    # Priorität 1: Premium Pipeline
    if "premium-headshot-pipeline" in model_registry:
        cost = model_registry["premium-headshot-pipeline"].cost
        special_btn_text = f"{base_text} ({cost} ⭐️)"
    # Priorität 2: Ultimate Pipeline
    elif "ultimate-headshot-pipeline" in model_registry:
        cost = model_registry["ultimate-headshot-pipeline"].cost
        special_btn_text = f"{base_text} ({cost} ⭐️)"
    # Priorität 3: Altes Instant-ID
    elif "instant-id" in model_registry:
        cost = model_registry["instant-id"].cost
        special_btn_text = f"{base_text} ({cost} ⭐️)"

    btn_special = types.KeyboardButton(special_btn_text)
    
    # 2. SUBMENÜS (Navigations-Buttons mit Übersetzung)
    btn_img = types.KeyboardButton(get_text("menu_image_studio", lang))
    btn_img_desc = types.KeyboardButton(get_text("menu_image_description", lang))
    btn_vid = types.KeyboardButton(get_text("menu_video_studio", lang))
    btn_tools = types.KeyboardButton(get_text("menu_tools_edit", lang))
    
    # NEU: Free Credits / Referral Button
    btn_free = types.KeyboardButton(get_text("btn_free_credits", lang))
    
    markup.add(btn_special)             
    markup.add(btn_img, btn_vid)        
    markup.add(btn_img_desc)               
    markup.add(btn_tools, btn_free)  # Hier den neuen Button hinzugefügt

    return markup

def _create_dynamic_menu(model_registry: dict, filter_types: list, lang: str, row_width=2):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)
    buttons = []
    
    for key, model in model_registry.items():
        if any(t in model.type for t in filter_types):
            # Pipeline Modelle oft ausblenden in Submenüs
            if "pipeline" in model.type and len(filter_types) == 1 and "image" in filter_types:
                 continue 
            
            # Button Text formatieren
            btn_text = f"{model.name} ({model.cost} ⭐️)"
            buttons.append(types.KeyboardButton(btn_text))
            
    markup.add(*buttons)
    markup.add(types.KeyboardButton(get_text("btn_back", lang)))
    return markup

def get_image_studio_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["image"], lang=lang, row_width=2)

def get_image_description_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["image_analysis"], lang=lang, row_width=2)


def get_video_studio_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["video"], lang=lang, row_width=1)

def get_edit_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["edit", "upscale", "analysis"], lang=lang, row_width=2)

# --- NEU: Einfaches Menü nur mit "Zurück" ---
def get_back_menu(lang: str = "de"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton(get_text("btn_back", lang)))
    return markup

# --- NEU: Social Media Share Keyboard ---
def get_share_menu(ref_link: str, share_text: str, lang: str = "de"):
    """Erstellt Inline-Buttons mit Links zu den sozialen Netzwerken"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # URL-Encoding für die Share-Links
    encoded_url = quote(ref_link)
    encoded_text = quote(share_text)
    
    # Intent URLs für schnelles Teilen
    url_tg = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"
    url_vk = f"https://vk.com/share.php?url={encoded_url}&title={encoded_text}"
    url_x = f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_text}"
    url_fb = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    url_ok = f"https://connect.ok.ru/offer?url={encoded_url}&title={encoded_text}"

    btn_tg = types.InlineKeyboardButton(get_text("btn_share_tg", lang), url=url_tg)
    btn_vk = types.InlineKeyboardButton(get_text("btn_share_vk", lang), url=url_vk)
    btn_x = types.InlineKeyboardButton(get_text("btn_share_x", lang), url=url_x)
    btn_fb = types.InlineKeyboardButton(get_text("btn_share_fb", lang), url=url_fb)
    btn_ok = types.InlineKeyboardButton(get_text("btn_share_ok", lang), url=url_ok)

    markup.add(btn_tg)
    markup.add(btn_vk, btn_x)
    markup.add(btn_fb, btn_ok)
    
    return markup