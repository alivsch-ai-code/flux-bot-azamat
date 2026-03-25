"""Tests für src.config.settings – Settings-Klasse."""


class TestSettings:
    """Prüft Settings: Konfiguration (conftest setzt TELEGRAM_TOKEN, REPLICATE_API_TOKEN)."""

    def test_config_loads_with_valid_env(self):
        """Mit gesetzten Vars lädt config korrekt."""
        from src.config.settings import config
        assert config.TELEGRAM_TOKEN
        assert config.REPLICATE_API_TOKEN
        assert config.PORT >= 1
        assert isinstance(config.APP_ENV, str)
        assert len(config.APP_ENV) > 0

    def test_start_credits_50(self):
        """START_CREDITS ist 50."""
        from src.config.settings import config
        assert config.START_CREDITS == 50

    def test_replicate_max_concurrent_at_least_1(self):
        """REPLICATE_MAX_CONCURRENT ist mindestens 1."""
        from src.config.settings import config
        assert config.REPLICATE_MAX_CONCURRENT >= 1

    def test_optional_api_keys_attributes_exist(self):
        """Optionale API-Keys sind als Attribute vorhanden (können None sein)."""
        from src.config.settings import config
        for key in ("SONAUTO_API_KEY", "KLING_API_KEY", "OPENAI_API_KEY"):
            assert hasattr(config, key)
