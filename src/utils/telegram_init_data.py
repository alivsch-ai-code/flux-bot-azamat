"""Validierung von Telegram Web App initData (HMAC-SHA256)."""
import hmac
import hashlib
from urllib.parse import parse_qs


def validate_init_data(init_data: str, bot_token: str) -> int | None:
    """
    Validiert initData von Telegram.WebApp.initData.
    Gibt User-Daten zurück oder None bei Ungültigkeit.
    """
    if not init_data or not bot_token:
        return None
    try:
        parsed = parse_qs(init_data, keep_blank_values=True)
        hash_val = parsed.get("hash", [None])[0]
        if not hash_val:
            return None
        data_check_string = "\n".join(
            f"{k}={v[0]}" for k, v in sorted(parsed.items()) if k != "hash"
        )
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        calculated = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(calculated, hash_val):
            return None
        import json
        user_str = parsed.get("user", [None])[0]
        if user_str:
            user = json.loads(user_str)
            return int(user.get("id", 0))
        return None
    except Exception:
        return None
