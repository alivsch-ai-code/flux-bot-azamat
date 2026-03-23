"""Tests für src.utils.gimmicks."""
from src.utils.gimmicks import get_random_tip, TIPS_DICT


class TestGetRandomTip:
    def test_returns_string(self):
        result = get_random_tip("de")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_german_tips_contain_keywords(self):
        for _ in range(10):  # mehrfach, da zufällig
            tip = get_random_tip("de")
            assert "Tipp" in tip or "b>" in tip or "💡" in tip or "🚀" in tip

    def test_unknown_lang_fallback_to_en(self):
        result = get_random_tip("xy")
        assert isinstance(result, str)
        assert result in TIPS_DICT["en"]

    def test_all_supported_languages(self):
        for lang in ("de", "en", "ru", "kk"):
            tip = get_random_tip(lang)
            assert tip in TIPS_DICT.get(lang, TIPS_DICT["en"])
