"""Tests für src.presentation.telegram.handlers.common – In-Memory Dialog-State."""
from src.presentation.telegram.handlers.common import (
    get_context,
    set_context,
    clear_context,
)


class TestCommonContext:
    """Prüft get_context, set_context, clear_context (thread-sicherer User-State)."""

    def test_get_context_empty_returns_empty_dict(self):
        """Frischer User hat leeren Kontext."""
        clear_context(999888)
        assert get_context(999888) == {}

    def test_set_and_get_context(self):
        """set_context speichert Daten, get_context liefert Kopie."""
        uid = 888777
        clear_context(uid)
        set_context(uid, {"step": "waiting", "model_key": "flux"})
        ctx = get_context(uid)
        assert ctx == {"step": "waiting", "model_key": "flux"}
        assert ctx is not get_context(uid)

    def test_get_returns_copy(self):
        """get_context liefert Kopie – Modifikation ändert nicht den gespeicherten Zustand."""
        uid = 777666
        clear_context(uid)
        set_context(uid, {"a": 1})
        ctx1 = get_context(uid)
        ctx1["b"] = 2
        ctx2 = get_context(uid)
        assert ctx2 == {"a": 1}

    def test_clear_context_removes_data(self):
        """clear_context entfernt den Eintrag."""
        uid = 666555
        set_context(uid, {"x": 1})
        assert get_context(uid) == {"x": 1}
        clear_context(uid)
        assert get_context(uid) == {}

    def test_clear_nonexistent_is_safe(self):
        """clear_context bei nicht vorhandenem User ist harmlos."""
        clear_context(999999999)
