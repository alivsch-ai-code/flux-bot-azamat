from urllib.parse import quote

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

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


def _truncate_callback_data(data: str, max_bytes: int = 64) -> str:
    """Telegram erlaubt callback_data nur 1–64 Bytes."""
    enc = data.encode("utf-8")
    if len(enc) <= max_bytes:
        return data
    while len(enc) > max_bytes and data:
        data = data[:-1]
        enc = data.encode("utf-8")
    return data if data else "err"


def btn(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=_truncate_callback_data(callback_data))


def _folder_sort_key(cat: str) -> tuple[int, str]:
    c = (cat or "").strip().lower()
    if c in ("favorites", "favoriten", "favourites"):
        return (0, c)
    return (1, c)


def get_dynamic_model_menu(
    models: list, lang: str = "de", current_path: str = "root"
) -> InlineKeyboardMarkup:
    sub_categories = set()
    model_buttons: list[InlineKeyboardButton] = []

    for m in models:
        is_in_current_path = False

        if m.menu_path == current_path:
            is_in_current_path = True
        elif current_path == "root" and "/" not in m.menu_path and m.menu_path != "root":
            sub_categories.add(m.menu_path)
            continue
        elif m.menu_path.startswith(current_path + "/"):
            relative = m.menu_path[len(current_path) + 1 :]
            next_folder = relative.split("/")[0]
            sub_categories.add(next_folder)
            continue
        elif current_path == "root" and m.menu_path == "root":
            is_in_current_path = True

        if is_in_current_path:
            cost_display = f"({m.final_cost} ⭐️)" if m.final_cost > 0 else "(FREE)"
            model_buttons.append(btn(f"{m.name} {cost_display}", f"sel_{m.key}"))

    rows: list[list[InlineKeyboardButton]] = []

    folder_buttons = []
    for cat in sorted(sub_categories, key=_folder_sort_key):
        display_name = get_text(f"menu_{cat}", lang)
        if display_name.startswith("menu_"):
            display_name = cat.capitalize()
        target_path = cat if current_path == "root" else f"{current_path}/{cat}"
        folder_buttons.append(btn(f"📁 {display_name}", f"nav_path_{target_path}"))

    if folder_buttons:
        rows.append(folder_buttons)

    for mb in model_buttons:
        rows.append([mb])

    if current_path != "root":
        if "/" in current_path:
            parent = current_path.rsplit("/", 1)[0]
        else:
            parent = "root"
        rows.append([btn(get_text("btn_back", lang), f"nav_path_{parent}")])
    else:
        rows.append(
            [
                btn(get_text("menu_profile", lang), "nav_profile"),
                btn(get_text("menu_settings", lang), "nav_settings"),
            ]
        )
        rows.append([btn(get_text("menu_shop", lang), "cmd_shop")])
        rows.append([btn(get_text("menu_referral", lang), "nav_referral")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_chat_mode_ask_menu(model_key: str, lang: str = "de") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                btn(get_text("btn_yes_chat", lang), f"chat_mode_yes_{model_key}"),
                btn(get_text("btn_no_chat", lang), f"chat_mode_no_{model_key}"),
            ],
            [btn(get_text("btn_back", lang), "nav_path_text")],
        ]
    )


def get_chat_active_menu(lang: str = "de") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[btn(get_text("btn_end_chat", lang), "stop_chat")]])


def get_settings_menu(settings: dict, lang: str = "de") -> InlineKeyboardMarkup:
    lang_label = "🇩🇪 Deutsch" if lang == "de" else ("🇬🇧 English" if lang == "en" else "🇷🇺 Русский")
    opt_txt = get_text("btn_opt_on", lang) if settings.get("auto_opt", True) else get_text("btn_opt_off", lang)
    neg_txt = (
        get_text("btn_neg_on", lang)
        if settings.get("auto_negative_prompt", True)
        else get_text("btn_neg_off", lang)
    )
    daily_txt = get_text("btn_daily_on", lang) if settings.get("daily_msg", True) else get_text("btn_daily_off", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [btn(get_text("btn_lang", lang).format(lang=lang_label), "nav_lang")],
            [btn(opt_txt, "toggle_opt")],
            [btn(neg_txt, "toggle_neg")],
            [btn(daily_txt, "toggle_daily")],
            [btn(get_text("btn_clear_history", lang), "clear_history")],
            [btn(get_text("btn_back", lang), "nav_main")],
        ]
    )


def get_language_menu(lang: str = "de") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                btn("🇩🇪 Deutsch", "set_lang_de"),
                btn("🇬🇧 English", "set_lang_en"),
            ],
            [
                btn("🇷🇺 Русский", "set_lang_ru"),
                btn("🇰🇿 Қазақша", "set_lang_kk"),
            ],
            [btn(get_text("btn_back", lang), "nav_settings")],
        ]
    )


def get_back_menu(lang: str = "de", target: str = "nav_path_root") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[btn(get_text("btn_back", lang), target)]])


def get_image_loop_buttons(
    lang: str,
    menu_mode: str,
    webapp_url: str,
    model_key: str,
    menu_path: str,
) -> InlineKeyboardMarkup:
    if menu_mode == "webapp" and webapp_url:
        base = webapp_url.rstrip("/")
        back_path = menu_path or "image"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=get_text("btn_back", lang),
                        web_app=WebAppInfo(url=f"{base}/webapp?path={back_path}"),
                    ),
                    InlineKeyboardButton(
                        text=get_text("kb_main", lang),
                        web_app=WebAppInfo(url=f"{base}/webapp?path=root"),
                    ),
                ]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                btn(get_text("btn_back", lang), f"sel_{model_key}"),
                btn(get_text("kb_main", lang), "nav_path_root"),
            ]
        ]
    )


def get_share_menu(link: str, text: str, lang: str = "en") -> InlineKeyboardMarkup:
    url = f"https://t.me/share/url?url={quote(link)}&text={quote(text)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_share_tg", lang), url=url)],
            [btn(get_text("btn_back", lang), "nav_profile")],
        ]
    )


def get_main_reply_keyboard(lang: str = "de") -> ReplyKeyboardMarkup:
    row1 = [get_text(k, lang) for _, k in KEYBOARD_ACTIONS if k.startswith("menu_") and k not in ("menu_shop", "menu_profile")]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t) for t in row1],
            [
                KeyboardButton(text=get_text("menu_shop", lang)),
                KeyboardButton(text=get_text("menu_profile", lang)),
                KeyboardButton(text=get_text("kb_main", lang)),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_keyboard_action_for_text(text: str) -> str | None:
    if not text or not text.strip():
        return None
    text = text.strip()
    for action, key in KEYBOARD_ACTIONS:
        for loc in ("de", "en", "ru", "kk"):
            if get_text(key, loc) == text:
                return action
    return None


def get_path_reply_keyboard(
    models: list, lang: str, current_path: str
) -> ReplyKeyboardMarkup:
    sub_categories = set()
    model_buttons: list[tuple[str, str]] = []

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

    keyboard: list[list[KeyboardButton]] = []

    for cat in sorted(sub_categories, key=_folder_sort_key):
        display = get_text(f"menu_{cat}", lang)
        if display.startswith("menu_"):
            display = cat.capitalize()
        keyboard.append([KeyboardButton(text=f"📁 {display}")])

    model_buttons.sort(key=lambda x: x[0].lower())
    for i in range(0, len(model_buttons), 2):
        row = [KeyboardButton(text=t) for t, _ in model_buttons[i : i + 2]]
        keyboard.append(row)

    keyboard.append(
        [
            KeyboardButton(text=get_text("btn_back", lang)),
            KeyboardButton(text=get_text("kb_main", lang)),
        ]
    )

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)


def get_path_keyboard_action(
    text: str, current_path: str, models: list, lang: str
) -> tuple[str, str] | None:
    if not text or not text.strip():
        return None
    t = text.strip()
    for loc in ("de", "en", "ru", "kk"):
        if get_text("btn_back", loc) == t:
            if "/" in current_path:
                parent = current_path.rsplit("/", 1)[0]
                return ("nav_path", parent)
            return ("nav_main", "")
        if get_text("kb_main", loc) == t:
            return ("nav_main", "")

    sub_categories = set()
    for m in models:
        if current_path == "root" and "/" not in m.menu_path and m.menu_path != "root":
            sub_categories.add(m.menu_path)
        elif m.menu_path.startswith(current_path + "/"):
            rel = m.menu_path[len(current_path) + 1 :]
            sub_categories.add(rel.split("/")[0])

    for cat in sorted(sub_categories, key=_folder_sort_key):
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
