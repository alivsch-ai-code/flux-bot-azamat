"""Tests für src.utils.telegram_init_data (initData-Validierung)."""
from src.utils.telegram_init_data import validate_init_data


class TestValidateInitData:
    def test_empty_init_data_returns_none(self):
        assert validate_init_data("", "any_token") is None

    def test_empty_token_returns_none(self):
        assert validate_init_data("user=%7B%22id%22%3A123%7D", "") is None

    def test_both_empty_returns_none(self):
        assert validate_init_data("", "") is None

    def test_invalid_hash_returns_none(self):
        # Korrekte Struktur, aber falscher Hash
        bad = "user=%7B%22id%22%3A12345%7D&hash=invalid_hash_value"
        assert validate_init_data(bad, "some_bot_token") is None

    def test_missing_hash_returns_none(self):
        bad = "user=%7B%22id%22%3A12345%7D"
        assert validate_init_data(bad, "some_bot_token") is None

    def test_malformed_json_returns_none(self):
        # Hash würde nie passen, aber auch kein gültiger user
        bad = "user=not_valid_json&hash=abc"
        assert validate_init_data(bad, "token") is None
