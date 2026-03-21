from urllib.parse import quote

from telebot import types

from src.utils.strings import get_text

# Mapping: action -> string key für Reply-Keyboard-Buttons
KEYBOARD_ACTIONS = [
    ("nav_main", "kb_main"),
    ("nav_path_image", "menu_image"),
    ("nav_path_video", "menu_video"),
    ("nav_path_audio", "menu_audio"),
    ("nav_path_text", "menu_text"),
    ("nav_path_tools", "menu_tools"),
    ("cmd_shop", "menu_shop"),
    ("nav_profile", "menu_profile"),
]


def btn(text: str, callback_data: str) -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton(text=text, callback_data=callback_data)

# --- DYNAMISCHES MENÜ SYSTEM ---
def get_dynamic_model_menu(
    models: list, lang: str = "de", current_path: str = "root"
) -> types.InlineKeyboardMarkup:
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
        if display_name.startswith("menu_"):
            display_name = cat.capitalize()
        
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
        markup.add(
            btn(get_text("menu_profile", lang), "nav_profile"),
            btn(get_text("menu_settings", lang), "nav_settings"),
        )
        markup.add(btn(get_text("menu_shop", lang), "cmd_shop"))
        markup.add(btn(get_text("menu_referral", lang), "nav_referral"))

    return markup

# --- CHAT MODE MENÜS ---
def get_chat_mode_ask_menu(model_key: str, lang: str = "de") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn(get_text("btn_yes_chat", lang), f"chat_mode_yes_{model_key}"),
        btn(get_text("btn_no_chat", lang), f"chat_mode_no_{model_key}"),
    )
    markup.add(btn(get_text("btn_back", lang), "nav_path_text"))
    return markup

def get_chat_active_menu(lang: str = "de") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(get_text("btn_end_chat", lang), "stop_chat"))
    return markup

# --- SETTINGS & HELPER MENUS ---
def get_settings_menu(settings: dict, lang: str = "de") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    lang_label = "🇩🇪 Deutsch" if lang == "de" else ("🇬🇧 English" if lang == "en" else "🇷🇺 Русский")
    markup.add(btn(get_text("btn_lang", lang).format(lang=lang_label), "nav_lang"))
    
    opt_txt = get_text("btn_opt_on", lang) if settings.get("auto_opt", True) else get_text("btn_opt_off", lang)
    markup.add(btn(opt_txt, "toggle_opt"))
    
    daily_txt = get_text("btn_daily_on", lang) if settings.get("daily_msg", True) else get_text("btn_daily_off", lang)
    markup.add(btn(daily_txt, "toggle_daily"))

    markup.add(btn(get_text("btn_back", lang), "nav_main"))
    return markup

def get_language_menu(lang: str = "de") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("🇩🇪 Deutsch", "set_lang_de"),
        btn("🇬🇧 English", "set_lang_en"),
        btn("🇷🇺 Русский", "set_lang_ru"),
        btn("🇰🇿 Қазақша", "set_lang_kk"),
    )
    markup.add(btn(get_text("btn_back", lang), "nav_settings"))
    return markup

def get_back_menu(lang: str = "de", target: str = "nav_path_root") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(get_text("btn_back", lang), target))
    return markup


def get_image_loop_buttons(
    lang: str,
    menu_mode: str,
    webapp_url: str,
    model_key: str,
    menu_path: str,
) -> types.InlineKeyboardMarkup:
    """
    Zurück + Hauptmenü nach Bildgenerierung.
    Im WebApp-Modus: Buttons öffnen die Mini App (Zurück = Kategorie, Hauptmenü = Root).
    """
    if menu_mode == "webapp" and webapp_url:
        base = webapp_url.rstrip("/")
        back_path = menu_path or "image"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                get_text("btn_back", lang),
                web_app=types.WebAppInfo(url=f"{base}/webapp?path={back_path}"),
            ),
            types.InlineKeyboardButton(
                get_text("kb_main", lang),
                web_app=types.WebAppInfo(url=f"{base}/webapp?path=root"),
            ),
        )
        return markup
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn(get_text("btn_back", lang), f"sel_{model_key}"),
        btn(get_text("kb_main", lang), "nav_path_root"),
    )
    return markup

def get_share_menu(link: str, text: str, lang: str = "en") -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    url = f"https://t.me/share/url?url={quote(link)}&text={quote(text)}"
    markup.add(types.InlineKeyboardButton(get_text("btn_share_tg", lang), url=url))
    markup.add(btn(get_text("btn_back", lang), "nav_profile"))
    return markup


# --- REPLY KEYBOARD (Tastatur direkt unter dem Eingabefeld) ---
def get_main_reply_keyboard(lang: str = "de") -> types.ReplyKeyboardMarkup:
    """Persistente Tastatur mit Hauptmenü-Shortcuts. Nur wenn menu_mode=keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    # Zeile 1: Medien-Kategorien
    row1 = [get_text(k, lang) for _, k in KEYBOARD_ACTIONS if k.startswith("menu_") and k not in ("menu_shop", "menu_profile")]
    markup.row(*[types.KeyboardButton(t) for t in row1])
    # Zeile 2: Credits, Profil, Hauptmenü
    markup.row(
        types.KeyboardButton(get_text("menu_shop", lang)),
        types.KeyboardButton(get_text("menu_profile", lang)),
        types.KeyboardButton(get_text("kb_main", lang)),
    )
    return markup


def get_keyboard_action_for_text(text: str) -> str | None:
    """Mappt gesendeten Tastatur-Button-Text auf die Action. None wenn kein Treffer."""
    if not text or not text.strip():
        return None
    text = text.strip()
    for action, key in KEYBOARD_ACTIONS:
        for lang in ("de", "en", "ru", "kk"):
            if get_text(key, lang) == text:
                return action
    return None


def get_path_reply_keyboard(
    models: list, lang: str, current_path: str
) -> types.ReplyKeyboardMarkup:
    """Reply-Keyboard für Untermenü (Ordner + Modelle + Zurück/Hauptmenü)."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    sub_categories = set()
    model_buttons = []

    for m in models:
        if m.menu_path == current_path:
            cost_display = f"({m.final_cost} ⭐️)" if m.final_cost > 0 else "(FREE)"
            model_buttons.append((f"{m.name} {cost_display}", m.key))
        elif current_path == "root" and "/" not in m.menu_path and m.menu_path != "root":
            sub_categories.add(m.menu_path)
        elif m.menu_path.startswith(current_path + "/"):
            rel = m.menu_path[len(current_path) + 1 :]
            sub_categories.add(rel.split("/")[0])
        elif current_path == "root" and m.menu_path == "root":
            cost_display = f"({m.final_cost} ⭐️)" if m.final_cost > 0 else "(FREE)"
            model_buttons.append((f"{m.name} {cost_display}", m.key))

    for cat in sorted(sub_categories):
        display = get_text(f"menu_{cat}", lang)
        if display.startswith("menu_"):
            display = cat.capitalize()
        markup.row(types.KeyboardButton(f"📁 {display}"))

    for i in range(0, len(model_buttons), 2):
        row = [types.KeyboardButton(t) for t, _ in model_buttons[i : i + 2]]
        markup.row(*row)

    markup.row(
        types.KeyboardButton(get_text("btn_back", lang)),
        types.KeyboardButton(get_text("kb_main", lang)),
    )
    return markup


def get_path_keyboard_action(
    text: str, current_path: str, models: list, lang: str
) -> tuple[str, str] | None:
    """Liefert (action_type, target) für Path-Tastatur. action_type: nav_path, sel, nav_main, back."""
    if not text or not text.strip():
        return None
    t = text.strip()
    back_text = get_text("btn_back", lang)
    main_text = get_text("kb_main", lang)
    for l in ("de", "en", "ru", "kk"):
        if get_text("btn_back", l) == t:
            if "/" in current_path:
                parent = current_path.rsplit("/", 1)[0]
                return ("nav_path", parent)  # z.B. image/flux -> image
            return ("nav_main", "")  # image -> Hauptmenü
        if get_text("kb_main", l) == t:
            return ("nav_main", "")

    sub_categories = set()
    for m in models:
        if current_path == "root" and "/" not in m.menu_path and m.menu_path != "root":
            sub_categories.add(m.menu_path)
        elif m.menu_path.startswith(current_path + "/"):
            rel = m.menu_path[len(current_path) + 1 :]
            sub_categories.add(rel.split("/")[0])

    for cat in sorted(sub_categories):
        display = get_text(f"menu_{cat}", lang)
        if display.startswith("menu_"):
            display = cat.capitalize()
        if t == f"📁 {display}":
            target = cat if current_path == "root" else f"{current_path}/{cat}"
            return ("nav_path", target)

    for m in models:
        if m.menu_path == current_path or (current_path == "root" and m.menu_path == "root"):
            cost_display = f"({m.final_cost} ⭐️)" if m.final_cost > 0 else "(FREE)"
            if t == f"{m.name} {cost_display}":
                return ("sel", m.key)

    return None