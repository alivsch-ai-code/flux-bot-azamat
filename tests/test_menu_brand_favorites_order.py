from types import SimpleNamespace

from src.presentation.telegram import keyboards


def _model(key: str, name: str, menu_path: str, cost: int = 1):
    return SimpleNamespace(
        key=key,
        name=name,
        menu_path=menu_path,
        final_cost=cost,
    )


def test_dynamic_menu_sorts_favorites_folder_first():
    models = [
        _model("m1", "Flux Dev", "image/flux"),
        _model("m2", "Google Nano", "image/google"),
        _model("m3", "Fav One", "image/favorites"),
    ]

    markup = keyboards.get_dynamic_model_menu(models, lang="de", current_path="image")

    folder_buttons = [
        btn
        for row in markup.inline_keyboard
        for btn in row
        if getattr(btn, "callback_data", "").startswith("nav_path_image/")
    ]
    assert folder_buttons, "Expected folder buttons under image path"
    assert folder_buttons[0].callback_data == "nav_path_image/favorites"


def test_path_reply_keyboard_sorts_favorites_folder_first():
    models = [
        _model("m1", "Flux Dev", "image/flux"),
        _model("m2", "Google Nano", "image/google"),
        _model("m3", "Fav One", "image/favorites"),
    ]

    markup = keyboards.get_path_reply_keyboard(models, lang="de", current_path="image")
    texts = []
    for row in markup.keyboard:
        for btn in row:
            if isinstance(btn, dict):
                texts.append(btn.get("text", ""))
            else:
                texts.append(getattr(btn, "text", ""))
    folder_texts = [t for t in texts if t.startswith("📁 ")]
    assert folder_texts
    assert "Favoriten" in folder_texts[0] or "Favorites" in folder_texts[0]

