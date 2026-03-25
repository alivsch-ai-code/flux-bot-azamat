"""Tests: DatabaseManager.update_credits schreibt in die transactions-Tabelle."""
from unittest.mock import MagicMock, patch

import pytest


@patch("src.infrastructure.database.psycopg2.connect")
def test_update_credits_inserts_into_transactions(mock_connect):
    """update_credits muss INSERT INTO transactions ausführen."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test:test@localhost/test"}, clear=False):
        from src.infrastructure.database import DatabaseManager

        db = DatabaseManager()
        db.update_credits(user_id=99999, amount=-10, reason="gen_flux-test")

    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("transactions" in c and "INSERT" in c for c in calls)
    # Prüfe, dass die richtigen Werte für transactions übergeben werden
    for call in mock_cursor.execute.call_args_list:
        args = call[0]
        if len(args) >= 1 and "transactions" in str(args[0]) and "INSERT" in str(args[0]):
            params = args[1] if len(args) > 1 else ()
            assert 99999 in params
            assert -10 in params
            assert "gen_flux-test" in params
            break
    else:
        pytest.fail("INSERT INTO transactions wurde nicht mit erwarteten Parametern aufgerufen")
    assert mock_conn.commit.called
