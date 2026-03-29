"""Regression: Telegram-Channel-Metadaten in derselben DB (telegram_channels), ohne zweite URL."""

import os
from unittest.mock import patch

def test_telegram_channel_methods_noop_when_database_url_missing():
    """Ohne Pool: keine Exceptions, leere/false Defaults."""
    with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
        from src.infrastructure.database import DatabaseManager

        db = DatabaseManager()
        db.upsert_telegram_channel(-1, "channel", title="x", username=None, treat_as_group=True, language="de")
        db.set_telegram_channel_receive_daily_news(-1, True)
        assert db.list_telegram_channels() == []
        assert db.get_telegram_channel_row(-1) is None
        assert db.should_skip_channel_from_group_daily(-1) is False
        assert db.iter_telegram_channels_daily_news() == []


def test_daily_service_constructor_accepts_no_channels_registry_kwarg():
    """channels_registry-Parameter entfernt — Aufruf mit 3 Args."""
    from unittest.mock import MagicMock

    from src.application.daily_services import DailyService

    bot = MagicMock()
    db = MagicMock()
    gen = MagicMock()
    svc = DailyService(bot, db, gen)
    assert svc.db is db
    assert svc.bot is bot
