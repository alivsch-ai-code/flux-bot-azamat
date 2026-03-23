"""Tests für src.utils.strings."""
from src.utils.strings import (
    get_text,
    get_welcome,
    get_webapp_strings,
    get_random_daily_fallback,
)


class TestGetText:
    def test_existing_key_en(self):
        assert "Back" in get_text("btn_back", "en")
        assert "Zurück" in get_text("btn_back", "de")

    def test_existing_key_fallback_to_en(self):
        # unbekannte Sprache -> Fallback auf en
        result = get_text("btn_back", "xy")
        assert result and len(result) > 0

    def test_unknown_key_returns_key(self):
        assert get_text("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"

    def test_nested_key_welcome(self):
        text = get_text("welcome", "de")
        assert "AZAMAT" in text and "Kasachstan" in text


class TestGetWelcome:
    def test_with_name(self):
        result = get_welcome("en", "Max")
        assert "Max" in result

    def test_without_name_fallback(self):
        result = get_welcome("en", None)
        assert "there" in result or "AZAMAT" in result

    def test_empty_name_uses_fallback(self):
        result = get_welcome("de", "   ")
        assert "du" in result or "AZAMAT" in result

    def test_all_locales_have_welcome(self):
        for lang in ("en", "de", "ru", "kk"):
            result = get_welcome(lang, "Test")
            assert result and "AZAMAT" in result


class TestGetWebappStrings:
    def test_returns_dict(self):
        result = get_webapp_strings("de")
        assert isinstance(result, dict)

    def test_contains_webapp_keys(self):
        result = get_webapp_strings("de")
        for key in ["webapp_title", "webapp_models", "webapp_back"]:
            assert key in result

    def test_values_not_empty(self):
        result = get_webapp_strings("en")
        for k, v in result.items():
            assert isinstance(v, str), f"{k} should be string"
            assert len(v) > 0, f"{k} should not be empty"


class TestGetRandomDailyFallback:
    def test_returns_string(self):
        result = get_random_daily_fallback("en", "User")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_name_when_given(self):
        result = get_random_daily_fallback("en", "Alice")
        assert "Alice" in result

    def test_handles_empty_name(self):
        result = get_random_daily_fallback("de", "")
        assert isinstance(result, str)
