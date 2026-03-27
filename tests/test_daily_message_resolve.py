import json

from src.application.daily_services import _resolve_daily_message_text


def test_resolve_plain_string_unchanged():
    s = "<b>Hi</b>"
    assert _resolve_daily_message_text(s, "de") == s


def test_resolve_json_picks_language():
    raw = json.dumps({"de": "Hallo", "en": "Hello", "ru": "Привет", "kk": "Сәлем"})
    assert _resolve_daily_message_text(raw, "ru") == "Привет"
    assert _resolve_daily_message_text(raw, "kk") == "Сәлем"


def test_resolve_json_fallback_en_then_de():
    raw = json.dumps({"en": "EN only"})
    assert _resolve_daily_message_text(raw, "ru") == "EN only"


def test_resolve_invalid_json_returns_raw():
    raw = "{not json"
    assert _resolve_daily_message_text(raw, "de") == raw


def test_daily_fallback_sent_date_key_stable():
    """Regression: Key für bot_settings muss stabil bleiben (Deploy-sichere 1×/Tag-Logik)."""
    from src.application.daily_services import BOT_SETTING_DAILY_FALLBACK_SENT_DATE

    assert BOT_SETTING_DAILY_FALLBACK_SENT_DATE == "daily_fallback_sent_date"
