from telebot import types
from src.utils.strings import get_text

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
    btn_vid = types.KeyboardButton(get_text("menu_video_studio", lang))
    btn_tools = types.KeyboardButton(get_text("menu_tools_edit", lang))
    
    markup.add(btn_special)             
    markup.add(btn_img, btn_vid)        
    markup.add(btn_tools)               

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

def get_video_studio_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["video"], lang=lang, row_width=1)

def get_edit_menu(model_registry: dict, lang: str = "de"):
    return _create_dynamic_menu(model_registry, filter_types=["edit", "upscale", "analysis"], lang=lang, row_width=2)

# --- NEU: Einfaches Menü nur mit "Zurück" ---
def get_back_menu(lang: str = "de"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton(get_text("btn_back", lang)))
    return markup