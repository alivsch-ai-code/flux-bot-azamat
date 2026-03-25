import os

import pytest
from unittest.mock import MagicMock, patch


def test_get_user_credits_closes_connection_on_execute_error():
    # Keine echte DB initialisieren
    with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
        from src.infrastructure.database import DatabaseManager

        db = DatabaseManager()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = RuntimeError("db_execute_failed")
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db, "_get_connection", return_value=mock_conn):
            with pytest.raises(RuntimeError, match="db_execute_failed"):
                db.get_user_credits(user_id=123)

        # Wichtig: Connection muss auch bei Exceptions geschlossen werden.
        assert mock_conn.close.called

