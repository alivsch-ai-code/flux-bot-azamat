"""Tests für src.infrastructure.ai.replicate.prompt_engineer – Fallback-Logik."""
from src.infrastructure.ai.replicate.prompt_engineer import _truncate_fallback


class TestTruncateFallback:
    """Prüft _truncate_fallback: Kürzt Konversation bei fehlgeschlagener LLM-Zusammenfassung."""

    def test_short_text_unchanged(self):
        """Kurzer Text bleibt unverändert."""
        text = "Short conversation."
        assert _truncate_fallback(text) == text

    def test_none_or_empty(self):
        """None/ leer ergibt leeren String bzw. ..."""
        assert _truncate_fallback(None) == ""
        assert _truncate_fallback("") == ""
        assert _truncate_fallback("   ") == ""

    def test_long_text_truncated(self):
        """Text > max_len wird gekürzt mit ... am Ende."""
        text = "x" * 600
        result = _truncate_fallback(text, max_len=500)
        assert len(result) == 503
        assert result.endswith("...")

    def test_custom_max_len(self):
        """max_len kann übergeben werden."""
        text = "a" * 200
        result = _truncate_fallback(text, max_len=50)
        assert len(result) == 53
        assert result.endswith("...")
