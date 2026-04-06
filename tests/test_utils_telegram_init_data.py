"""Tests für src.utils.telegram_init_data (initData-Validierung)."""
import hashlib
import hmac
import json
import time
from urllib.parse import quote_plus

from src.utils.telegram_init_data import validate_init_data


class TestValidateInitData:
    def _build_init_data(self, bot_token: str, user_id: int, auth_date: int) -> str:
        user_json = json.dumps({"id": user_id}, separators=(",", ":"))
        encoded_user = quote_plus(user_json)
        payload = f"auth_date={auth_date}&user={encoded_user}"
        data_check_string = f"auth_date={auth_date}\nuser={user_json}"
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return payload + f"&hash={signature}"

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

    def test_valid_signature_with_fresh_auth_date_returns_user_id(self):
        token = "bot_secret_token"
        uid = 123456
        init_data = self._build_init_data(token, uid, int(time.time()))
        assert validate_init_data(init_data, token) == uid

    def test_expired_auth_date_returns_none(self):
        token = "bot_secret_token"
        uid = 987654
        init_data = self._build_init_data(token, uid, int(time.time()) - 7200)
        assert validate_init_data(init_data, token) is None
