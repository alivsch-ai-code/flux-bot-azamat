from telebot import types
from src.utils.strings import get_text
from urllib.parse import quote

def btn(text, callback_data):
    return types.InlineKeyboardButton(text=text, callback_data=callback_data)

# --- DYNAMISCHES MENÜ SYSTEM ---
def get_dynamic_model_menu(models: list, lang: str = "de", current_path: str = "root"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    sub_categories = set()
    model_buttons = []
    
    for m in models:
        # Pfad-Logik
        is_in_current_path = False
        
        # Fall A: Direkt im Ordner (z.B. Path "video", Modell "video")
        if m.menu_path == current_path:
            is_in_current_path = True
            
        # Fall B: Im Root ohne Prefix
        elif current_path == "root" and "/" not in m.menu_path and m.menu_path != "root":
             # Das ist ein Ordner im Root (z.B. "video")
             sub_categories.add(m.menu_path)
             continue

        # Fall C: Unterordner Logik (z.B. "video/kling" wenn wir in "video" sind)
        elif m.menu_path.startswith(current_path + "/"):
            # Nächsten Ordner extrahieren
            relative = m.menu_path[len(current_path)+1:]
            next_folder = relative.split("/")[0]
            sub_categories.add(next_folder)
            continue
            
        # Fall D: Root Items
        elif current_path == "root" and m.menu_path == "root":
            is_in_current_path = True

        # Modell Button hinzufügen
        if is_in_current_path:
            # Hier nutzen wir jetzt m.final_cost (oder m.cost dank Property)
            cost_display = f"({m.final_cost} ⭐️)" if m.final_cost > 0 else "(FREE)"
            model_buttons.append(btn(f"{m.name} {cost_display}", f"sel_{m.key}"))

    # 1. Ordner-Buttons
    folder_buttons = []
    for cat in sorted(sub_categories):
        display_name = get_text(f"menu_{cat}", lang)
        # Fallback Name wenn keine Übersetzung
        if display_name.startswith("menu_"): display_name = cat.capitalize()
        
        target_path = cat if current_path == "root" else f"{current_path}/{cat}"
        folder_buttons.append(btn(f"📁 {display_name}", f"nav_path_{target_path}"))
    
    if folder_buttons:
        markup.add(*folder_buttons)

    # 2. Modell-Buttons
    if model_buttons:
        for mb in model_buttons:
            markup.add(mb)
    
    # 3. Navigation (Back/Shop/Profile)
    if current_path != "root":
        if "/" in current_path:
            parent = current_path.rsplit("/", 1)[0]
        else:
            parent = "root"
        markup.add(btn(get_text("btn_back", lang), f"nav_path_{parent}"))
    else:
        # Root Menü
        markup.add(
            btn(get_text("menu_profile", lang), "nav_profile"),
            btn(get_text("menu_settings", lang), "nav_settings")
        )
        markup.add(btn(get_text("menu_shop", lang), "cmd_shop"))
        markup.add(btn(get_text("menu_referral", lang), "nav_referral"))

    return markup

# --- CHAT MODE MENÜS ---
def get_chat_mode_ask_menu(model_key, lang="de"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn(get_text("btn_yes_chat", lang), f"chat_mode_yes_{model_key}"),
        btn(get_text("btn_no_chat", lang), f"chat_mode_no_{model_key}")
    )
    markup.add(btn(get_text("btn_back", lang), "nav_path_text"))
    return markup

def get_chat_active_menu(lang="de"):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(get_text("btn_end_chat", lang), "stop_chat"))
    return markup

# --- SETTINGS & HELPER MENUS ---
def get_settings_menu(settings: dict, lang: str = "de"):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    lang_label = "🇩🇪 Deutsch" if lang == "de" else ("🇬🇧 English" if lang == "en" else "🇷🇺 Русский")
    markup.add(btn(get_text("btn_lang", lang).format(lang=lang_label), "nav_lang"))
    
    opt_txt = get_text("btn_opt_on", lang) if settings.get("auto_opt", True) else get_text("btn_opt_off", lang)
    markup.add(btn(opt_txt, "toggle_opt"))
    
    daily_txt = get_text("btn_daily_on", lang) if settings.get("daily_msg", True) else get_text("btn_daily_off", lang)
    markup.add(btn(daily_txt, "toggle_daily"))

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

def get_back_menu(lang: str = "de", target="nav_path_root"):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(get_text("btn_back", lang), target))
    return markup

def get_share_menu(link, text, lang="en"):
    markup = types.InlineKeyboardMarkup()
    url = f"https://t.me/share/url?url={quote(link)}&text={quote(text)}"
    markup.add(types.InlineKeyboardButton(get_text("btn_share_tg", lang), url=url))
    markup.add(btn(get_text("btn_back", lang), "nav_profile"))
    return markup