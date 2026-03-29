"""
Separates Neon-Projekt für Telegram-Channels (optional).

Env: CHANNELS_DATABASE_URL — wenn leer, ist die Registry deaktiviert.

Erfasst u. a. chat_id, Telegram-Typ (channel/…), treat_as_group, receive_daily_news.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

import psycopg2
from psycopg2 import pool as psycopg2_pool

logger = logging.getLogger(__name__)


class _PooledConnectionProxy:
    def __init__(self, conn, owner):
        self._conn = conn
        self._owner = owner
        self._released = False

    def __getattr__(self, item):
        return getattr(self._conn, item)

    def close(self):
        if self._released:
            return
        self._released = True
        self._owner._release_connection(self._conn)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class ChannelsRegistry:
    """Kleiner Pool + Tabelle telegram_channels."""

    def __init__(self, dsn: str) -> None:
        self._dsn = (dsn or "").strip()
        self.lock = threading.Lock()
        self._pool: psycopg2_pool.ThreadedConnectionPool | None = None
        if self._dsn:
            self._pool = psycopg2_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=max(2, int(os.getenv("CHANNELS_DB_MAX_POOL_SIZE", "5"))),
                dsn=self._dsn,
                sslmode="require",
            )
            self._init_table()
        else:
            logger.warning("ChannelsRegistry: leere DSN")

    def is_configured(self) -> bool:
        return self._pool is not None

    def _release_connection(self, conn) -> None:
        if self._pool is not None:
            try:
                self._pool.putconn(conn)
                return
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass

    def _get_connection(self):
        if self._pool is not None:
            conn = self._pool.getconn()
            return _PooledConnectionProxy(conn, self)
        return psycopg2.connect(self._dsn, sslmode="require")

    def _init_table(self) -> None:
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telegram_channels (
                        chat_id BIGINT PRIMARY KEY,
                        telegram_chat_type TEXT NOT NULL,
                        title TEXT,
                        username TEXT,
                        treat_as_group INTEGER NOT NULL DEFAULT 0,
                        receive_daily_news INTEGER NOT NULL DEFAULT 0,
                        language TEXT NOT NULL DEFAULT 'de',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
                conn.commit()
            except Exception as e:
                logger.exception("ChannelsRegistry _init_table: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()

    def upsert_channel(
        self,
        chat_id: int,
        telegram_chat_type: str,
        *,
        title: str | None = None,
        username: str | None = None,
        treat_as_group: bool = False,
        language: str = "de",
        touch_receive_daily_news: bool = False,
        receive_daily_news: bool = False,
    ) -> None:
        """
        touch_receive_daily_news=False: Spalte receive_daily_news bleibt bei ON CONFLICT unverändert.
        """
        if not self._pool:
            return
        lang = language if language in ("de", "en", "ru", "kk") else "de"
        ctype = (telegram_chat_type or "channel").strip().lower()
        tg = 1 if treat_as_group else 0
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                if touch_receive_daily_news:
                    rd = 1 if receive_daily_news else 0
                    c.execute(
                        """
                        INSERT INTO telegram_channels (
                            chat_id, telegram_chat_type, title, username,
                            treat_as_group, receive_daily_news, language, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (chat_id) DO UPDATE SET
                            telegram_chat_type = EXCLUDED.telegram_chat_type,
                            title = EXCLUDED.title,
                            username = EXCLUDED.username,
                            treat_as_group = EXCLUDED.treat_as_group,
                            receive_daily_news = EXCLUDED.receive_daily_news,
                            language = EXCLUDED.language,
                            updated_at = NOW()
                        """,
                        (chat_id, ctype, title, username, tg, rd, lang),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO telegram_channels (
                            chat_id, telegram_chat_type, title, username,
                            treat_as_group, language, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (chat_id) DO UPDATE SET
                            telegram_chat_type = EXCLUDED.telegram_chat_type,
                            title = EXCLUDED.title,
                            username = EXCLUDED.username,
                            treat_as_group = EXCLUDED.treat_as_group,
                            language = EXCLUDED.language,
                            updated_at = NOW()
                        """,
                        (chat_id, ctype, title, username, tg, lang),
                    )
                conn.commit()
            except Exception as e:
                logger.warning("ChannelsRegistry upsert_channel failed: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()

    def set_receive_daily_news(self, chat_id: int, enabled: bool = True) -> None:
        if not self._pool:
            return
        v = 1 if enabled else 0
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    "UPDATE telegram_channels SET receive_daily_news = %s, updated_at = NOW() WHERE chat_id = %s",
                    (v, chat_id),
                )
                conn.commit()
            except Exception as e:
                logger.warning("ChannelsRegistry set_receive_daily_news failed: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()

    def should_skip_default_group_broadcast(self, chat_id: int) -> bool:
        """True: in Registry als channel erfasst → nicht über den normalen Gruppen-Daily-Loop."""
        if not self._pool:
            return False
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    "SELECT 1 FROM telegram_channels WHERE chat_id = %s AND telegram_chat_type = %s",
                    (int(chat_id), "channel"),
                )
                return c.fetchone() is not None
            except Exception as e:
                logger.warning("ChannelsRegistry should_skip_default_group_broadcast: %s", e)
                return False
            finally:
                conn.close()

    def iter_daily_news_channels(self) -> list[tuple[int, str]]:
        """Channels mit receive_daily_news=1."""
        if not self._pool:
            return []
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT chat_id, language FROM telegram_channels
                    WHERE receive_daily_news = 1 AND telegram_chat_type = 'channel'
                    """
                )
                rows = c.fetchall() or []
                out: list[tuple[int, str]] = []
                for r in rows:
                    try:
                        cid = int(r[0])
                        lang = (r[1] or "de").strip() or "de"
                        if lang not in ("de", "en", "ru", "kk"):
                            lang = "de"
                        out.append((cid, lang))
                    except Exception:
                        continue
                return out
            except Exception as e:
                logger.warning("ChannelsRegistry iter_daily_news_channels: %s", e)
                return []
            finally:
                conn.close()

    def list_all_rows(self) -> list[dict[str, Any]]:
        if not self._pool:
            return []
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT chat_id, telegram_chat_type, title, username, treat_as_group,
                           receive_daily_news, language
                    FROM telegram_channels
                    ORDER BY chat_id
                    """
                )
                rows = c.fetchall() or []
                out: list[dict[str, Any]] = []
                for row in rows:
                    out.append(
                        {
                            "chat_id": row[0],
                            "telegram_chat_type": row[1],
                            "title": row[2],
                            "username": row[3],
                            "treat_as_group": bool(row[4]),
                            "receive_daily_news": bool(row[5]),
                            "language": row[6] or "de",
                        }
                    )
                return out
            except Exception as e:
                logger.warning("ChannelsRegistry list_all_rows: %s", e)
                return []
            finally:
                conn.close()

    def get_row(self, chat_id: int) -> dict[str, Any] | None:
        if not self._pool:
            return None
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT chat_id, telegram_chat_type, title, username, treat_as_group,
                           receive_daily_news, language
                    FROM telegram_channels WHERE chat_id = %s
                    """,
                    (int(chat_id),),
                )
                row = c.fetchone()
                if not row:
                    return None
                return {
                    "chat_id": row[0],
                    "telegram_chat_type": row[1],
                    "title": row[2],
                    "username": row[3],
                    "treat_as_group": bool(row[4]),
                    "receive_daily_news": bool(row[5]),
                    "language": row[6] or "de",
                }
            except Exception as e:
                logger.warning("ChannelsRegistry get_row: %s", e)
                return None
            finally:
                conn.close()


def create_channels_registry() -> ChannelsRegistry | None:
    raw = (os.getenv("CHANNELS_DATABASE_URL") or "").strip()
    if not raw:
        return None
    try:
        reg = ChannelsRegistry(raw)
        if reg.is_configured():
            return reg
    except Exception as e:
        logger.exception("ChannelsRegistry konnte nicht initialisiert werden: %s", e)
    return None
