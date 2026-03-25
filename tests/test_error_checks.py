"""Tests für src.presentation.telegram.handlers.gen.error_checks."""
from src.presentation.telegram.handlers.gen.error_checks import (
    is_uri_too_large,
    is_rate_limit,
    is_technical_error,
)


class TestIsUriTooLarge:
    def test_414_in_message(self):
        assert is_uri_too_large("Error 414 Request-URI Too Large") is True

    def test_uri_too_large_phrase(self):
        assert is_uri_too_large("request-uri too large") is True

    def test_normal_error_false(self):
        assert is_uri_too_large("Something went wrong") is False


class TestIsRateLimit:
    def test_429_detected(self):
        assert is_rate_limit("429 Too Many Requests") is True

    def test_throttle_detected(self):
        assert is_rate_limit("throttled") is True

    def test_rate_limit_phrase(self):
        assert is_rate_limit("rate limit exceeded") is True

    def test_empty_false(self):
        assert is_rate_limit("") is False

    def test_normal_error_false(self):
        assert is_rate_limit("Internal server error") is False


class TestIsTechnicalError:
    def test_credits_not_technical(self):
        assert is_technical_error("not enough credits") is False

    def test_nsfw_not_technical(self):
        assert is_technical_error("NSFW content detected") is False

    def test_timeout_is_technical(self):
        assert is_technical_error("Connection timeout") is True

    def test_empty_false(self):
        assert is_technical_error("") is False
