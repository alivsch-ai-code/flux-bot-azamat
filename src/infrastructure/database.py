import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool as psycopg2_pool
import threading
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from src.domain.entities import User, AIModel

load_dotenv()
logger = logging.getLogger(__name__)


class _PooledConnectionProxy:
    """Gibt Connection beim close() an den Pool zurück."""

    def __init__(self, conn, owner):
        self._conn = conn
        self._owner = owner
        self._released = False

    def __getattr__(self, item):
        return getattr(self._conn, item)

    def close(self):
        # Idempotent: `close()` kann mehrfach aufgerufen werden
        # (z.B. durch explizites close() und späteres __del()).
        if self._released:
            return
        self._released = True
        self._owner._release_connection(self._conn)

    def __del__(self):
        """
        Fallback für Fehlpfade (z.B. Exception vor `conn.close()`):
        gibt die Connection so gut wie möglich ans Pool zurück.
        """
        try:
            self.close()
        except Exception:
            # Destructor darf nie Exceptions werfen.
            pass

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.lock = threading.RLock()
        self._pool = None
        
        if self.db_url:
            self._pool = psycopg2_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=int(os.getenv("DB_MAX_POOL_SIZE", "20")),
                dsn=self.db_url,
                sslmode="require",
            )
            self._init_db()
            self._migrate_db()
        else:
            logger.warning("DATABASE_URL fehlt in .env")

    def _get_connection(self):
        if self._pool is not None:
            conn = self._pool.getconn()
            return _PooledConnectionProxy(conn, self)
        return psycopg2.connect(self.db_url, sslmode='require')

    def _release_connection(self, conn):
        # Offene Transaktionen zurückrollen, bevor die Connection in den Pool geht.
        # Nach commit() ist rollback() ein No-Op – daher immer sicher.
        try:
            conn.rollback()
        except Exception:
            pass
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

    @contextmanager
    def _connection(self, commit: bool = False):
        """Liefert eine Connection und garantiert deren Freigabe.

        - commit=True: committet am Ende automatisch (Schreibzugriffe).
        - Bei Exceptions: Rollback, Connection wird trotzdem freigegeben.
        """
        conn = self._get_connection()
        try:
            yield conn
            if commit:
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                
                    # Users Tabelle
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username TEXT,
                            credits INTEGER DEFAULT 150,
                            language TEXT DEFAULT 'de',
                            auto_opt INTEGER DEFAULT 1,
                            auto_negative_prompt INTEGER DEFAULT 1,
                            daily_msg INTEGER DEFAULT 1,
                            last_model_key TEXT,
                            is_chat_mode INTEGER DEFAULT 0
                        )
                    ''')
                
                    # AI Models Tabelle (Full Schema)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS ai_models (
                            key TEXT PRIMARY KEY,
                            replicate_id TEXT,
                            name TEXT,
                            description TEXT,
                        
                            -- PREISE
                            base_cost_usd FLOAT DEFAULT 0.0,
                            internal_cost INTEGER DEFAULT 10,
                            custom_price INTEGER,
                        
                            -- METADATA
                            provider TEXT,
                            model_type TEXT, 
                            menu_path TEXT DEFAULT 'root',
                            is_active INTEGER DEFAULT 1,
                            is_favorite INTEGER DEFAULT 0,
                            is_commercial INTEGER DEFAULT 1,
                            manual_override INTEGER DEFAULT 0,
                        
                            -- JSON DATEN
                            input_schema JSONB,
                            output_schema JSONB,
                            example_data JSONB,
                        
                            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
                    # Transactions & Daily Posts
                    c.execute('''CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, user_id BIGINT, amount INTEGER, reason TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                    c.execute('''CREATE TABLE IF NOT EXISTS daily_posts (id SERIAL PRIMARY KEY, date_to_send TEXT UNIQUE, message_text TEXT, image_path TEXT, sent_status INTEGER DEFAULT 0)''')

                    # Generation Errors (Fehlermeldungen mit User/Modell; werden nach 7 Tagen gelöscht)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS generation_errors (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            model_key TEXT,
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    # Bot-Einstellungen (global, z.B. menu_mode: commands | keyboard)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS bot_settings (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL DEFAULT ''
                        )
                    ''')
                    # Gruppen-Einstellungen (Sprache pro Gruppe)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS group_settings (
                            chat_id BIGINT PRIMARY KEY,
                            language TEXT DEFAULT 'de'
                        )
                    ''')
                    # Einmalige Willkommens-DM an User aus Gruppen
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS group_greeting_sent (
                            user_id BIGINT PRIMARY KEY
                        )
                    ''')
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS group_greeting_attempted (
                            user_id BIGINT PRIMARY KEY
                        )
                    ''')
                    # Azamat 2x täglich Begrüßung (user_id, sent_date, slot)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS azamat_daily_sent (
                            user_id BIGINT NOT NULL,
                            sent_date TEXT NOT NULL,
                            slot INTEGER NOT NULL,
                            PRIMARY KEY (user_id, sent_date, slot)
                        )
                    ''')
                    # Azamat Random-Posts Zähler (Witz/Info pro Tag)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS azamat_random_count (
                            sent_date TEXT PRIMARY KEY, count INTEGER DEFAULT 0
                        )
                    ''')
                    # Gruppen-spezifische Credits pro User (Kauf über Gruppen-Button)
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS group_user_credits (
                            user_id BIGINT NOT NULL,
                            chat_id BIGINT NOT NULL,
                            credits INTEGER DEFAULT 0,
                            PRIMARY KEY (user_id, chat_id)
                        )
                    ''')
                    # Replicate async Predictions (Webhook): Zuordnung prediction_id → Telegram + Abrechnung
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS replicate_webhook_jobs (
                            prediction_id TEXT PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            model_key TEXT NOT NULL,
                            lang TEXT NOT NULL DEFAULT 'en',
                            effective_cost INTEGER NOT NULL,
                            no_charge INTEGER NOT NULL DEFAULT 0,
                            group_chat_id BIGINT,
                            is_chat INTEGER NOT NULL DEFAULT 0,
                            chat_history_mode TEXT,
                            user_prompt TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
            except Exception as e:
                logger.exception("DB Init Error: %s", e)

    def _migrate_db(self):
        """Fügt neue Spalten hinzu, falls sie in alten Tabellen fehlen."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            try:
                # 1. Migration für AI_MODELS
                model_cols = [
                    ("base_cost_usd", "FLOAT DEFAULT 0.0"),
                    ("internal_cost", "INTEGER DEFAULT 10"),
                    ("custom_price", "INTEGER"),
                    ("is_favorite", "INTEGER DEFAULT 0"),
                    ("is_commercial", "INTEGER DEFAULT 1"),
                    ("manual_override", "INTEGER DEFAULT 0"),
                    ("input_schema", "JSONB"),
                    ("output_schema", "JSONB"),
                    ("example_data", "JSONB"),
                    ("last_checked", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                ]
                for col, dtype in model_cols:
                    c.execute(f"ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS {col} {dtype}")

                # 2. Migration für USERS (WICHTIG für Chat Mode!)
                user_cols = [
                    ("last_model_key", "TEXT"),
                    ("is_chat_mode", "INTEGER DEFAULT 0"),
                    ("auto_negative_prompt", "INTEGER DEFAULT 1"),
                ]
                for col, dtype in user_cols:
                    c.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {dtype}")

                # 3. Bot-Settings Default: menu_mode (commands | keyboard | webapp)
                c.execute("SELECT 1 FROM bot_settings WHERE key = 'menu_mode'")
                if c.fetchone() is None:
                    c.execute("INSERT INTO bot_settings (key, value) VALUES ('menu_mode', 'commands')")

                # 4. Gruppen-Einstellungen (falls nicht in _init_db)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS group_settings (
                        chat_id BIGINT PRIMARY KEY,
                        language TEXT DEFAULT 'de'
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS group_greeting_sent (user_id BIGINT PRIMARY KEY)
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS group_greeting_attempted (user_id BIGINT PRIMARY KEY)
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS group_user_credits (
                        user_id BIGINT NOT NULL, chat_id BIGINT NOT NULL,
                        credits INTEGER DEFAULT 0, PRIMARY KEY (user_id, chat_id)
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS azamat_daily_sent (
                        user_id BIGINT NOT NULL, sent_date TEXT NOT NULL, slot INTEGER NOT NULL,
                        PRIMARY KEY (user_id, sent_date, slot)
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS azamat_random_count (
                        sent_date TEXT PRIMARY KEY, count INTEGER DEFAULT 0
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS replicate_webhook_jobs (
                        prediction_id TEXT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        model_key TEXT NOT NULL,
                        lang TEXT NOT NULL DEFAULT 'en',
                        effective_cost INTEGER NOT NULL,
                        no_charge INTEGER NOT NULL DEFAULT 0,
                        group_chat_id BIGINT,
                        is_chat INTEGER NOT NULL DEFAULT 0,
                        chat_history_mode TEXT,
                        user_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # AI-Daily-News: RSS-URLs in Neon (editierbar); leer beim ersten Start → Seed aus Code-Default.
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_news_rss_feeds (
                        id SERIAL PRIMARY KEY,
                        feed_url TEXT NOT NULL,
                        label TEXT,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT ai_news_rss_feeds_feed_url_key UNIQUE (feed_url)
                    )
                    """
                )
                c.execute("SELECT COUNT(*) FROM ai_news_rss_feeds")
                _rss_cnt = c.fetchone()
                if _rss_cnt and int(_rss_cnt[0]) == 0:
                    from src.application.ai_news_rss_defaults import AI_NEWS_RSS_DEFAULT_URLS

                    for _i, _url in enumerate(AI_NEWS_RSS_DEFAULT_URLS):
                        c.execute(
                            "INSERT INTO ai_news_rss_feeds (feed_url, sort_order) VALUES (%s, %s)",
                            (_url, _i),
                        )

                # Curated Kling-Modelle für neue Unterordner (idempotent via ON CONFLICT).
                # Ziel:
                # - video/motioncontrol: Bild + Video (Motion Transfer)
                # - video/avatar_sync: Bild + Audio (Avatar Lip Sync)
                # - tools/video_background_edit: Bild + Video (Background Edit)
                curated_models = [
                    {
                        "key": "kling-v3-motion-control",
                        "replicate_id": "kwaivgi/kling-v3-motion-control",
                        "name": "Kling v3 Motion Control",
                        "description": "Transfer motion from a source video onto a reference image.",
                        "internal_cost": 70,
                        "provider": "replicate",
                        "model_type": "video,image",
                        "menu_path": "video/motioncontrol",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "title": "Prompt"},
                                "input_image": {"type": "string", "format": "uri", "title": "Reference Image"},
                                "input_video": {"type": "string", "format": "uri", "title": "Motion Video"},
                            },
                            "required": ["input_image", "input_video"],
                        },
                        "output_schema": {"type": "string", "format": "uri"},
                        "example_data": {
                            "prompt": "Keep identity and outfit; transfer pose and camera motion from the video."
                        },
                    },
                    {
                        "key": "kling-v2-6-motion-control",
                        "replicate_id": "kwaivgi/kling-v2.6-motion-control",
                        "name": "Kling v2.6 Motion Control",
                        "description": "Transfer motion from a source video onto a reference image.",
                        "internal_cost": 65,
                        "provider": "replicate",
                        "model_type": "video,image",
                        "menu_path": "video/motioncontrol",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "title": "Prompt"},
                                "input_image": {"type": "string", "format": "uri", "title": "Reference Image"},
                                "input_video": {"type": "string", "format": "uri", "title": "Motion Video"},
                            },
                            "required": ["input_image", "input_video"],
                        },
                        "output_schema": {"type": "string", "format": "uri"},
                        "example_data": {
                            "prompt": "Transfer movement from the video while preserving character appearance."
                        },
                    },
                    {
                        "key": "kling-avatar-v2",
                        "replicate_id": "kwaivgi/kling-avatar-v2",
                        "name": "Kling Avatar v2",
                        "description": "Create speaking avatar video from a portrait image and an audio track.",
                        "internal_cost": 70,
                        "provider": "replicate",
                        "model_type": "video,image,audio",
                        "menu_path": "video/avatar_sync",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "title": "Prompt"},
                                "input_image": {"type": "string", "format": "uri", "title": "Avatar Image"},
                                "input_audio": {"type": "string", "format": "uri", "title": "Audio"},
                            },
                            "required": ["input_image", "input_audio"],
                        },
                        "output_schema": {"type": "string", "format": "uri"},
                        "example_data": {
                            "prompt": "Natural face movements, stable identity, clean lip-sync."
                        },
                    },
                    {
                        "key": "kling-o1-video-background-edit",
                        "replicate_id": "kwaivgi/kling-o1",
                        "name": "Kling O1 Video Background Edit",
                        "description": "Edit video background using a reference image and source video.",
                        "internal_cost": 65,
                        "provider": "replicate",
                        "model_type": "video,image",
                        "menu_path": "tools/video_background_edit",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "title": "Prompt"},
                                "input_image": {"type": "string", "format": "uri", "title": "Background Image"},
                                "input_video": {"type": "string", "format": "uri", "title": "Source Video"},
                            },
                            "required": ["input_image", "input_video"],
                        },
                        "output_schema": {"type": "string", "format": "uri"},
                        "example_data": {
                            "prompt": "Replace background with the image style, keep subject motion natural."
                        },
                    },
                ]
                for m in curated_models:
                    c.execute(
                        """
                        INSERT INTO ai_models (
                            key, replicate_id, name, description,
                            base_cost_usd, internal_cost, custom_price,
                            provider, model_type, menu_path, is_active, is_favorite,
                            is_commercial, manual_override, input_schema, output_schema, example_data
                        ) VALUES (
                            %s, %s, %s, %s,
                            0.0, %s, NULL,
                            %s, %s, %s, 1, 0,
                            1, 0, %s::jsonb, %s::jsonb, %s::jsonb
                        )
                        ON CONFLICT (key) DO UPDATE SET
                            replicate_id = EXCLUDED.replicate_id,
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            internal_cost = EXCLUDED.internal_cost,
                            provider = EXCLUDED.provider,
                            model_type = EXCLUDED.model_type,
                            menu_path = EXCLUDED.menu_path,
                            is_active = 1,
                            is_commercial = 1,
                            input_schema = EXCLUDED.input_schema,
                            output_schema = EXCLUDED.output_schema,
                            example_data = EXCLUDED.example_data
                        """,
                        (
                            m["key"],
                            m["replicate_id"],
                            m["name"],
                            m["description"],
                            m["internal_cost"],
                            m["provider"],
                            m["model_type"],
                            m["menu_path"],
                            json.dumps(m["input_schema"], ensure_ascii=False),
                            json.dumps(m["output_schema"], ensure_ascii=False),
                            json.dumps(m["example_data"], ensure_ascii=False),
                        ),
                    )

                # Seedance soll als eigener Ordner sichtbar sein (nicht nur Favoriten).
                c.execute(
                    """
                    UPDATE ai_models
                    SET menu_path = %s, last_checked = NOW()
                    WHERE key = %s OR replicate_id = %s
                    """,
                    ("video/bytedance/seedance", "bytedance-seedance-1.5-pro", "bytedance/seedance-1.5-pro"),
                )

                # Telegram-Kanäle (Metadaten + Daily-News Opt-in) — dieselbe Neon-DB wie der Rest.
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Performance-Indizes für häufige Filter.
                c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_generation_errors_user_id ON generation_errors (user_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_replicate_webhook_jobs_user_id ON replicate_webhook_jobs (user_id)")

                # daily_posts: DATE-Spalte für robuste Datumsfilter (legacy TEXT bleibt kompatibel).
                c.execute("ALTER TABLE daily_posts ADD COLUMN IF NOT EXISTS date_to_send_date DATE")
                c.execute(
                    """
                    UPDATE daily_posts
                    SET date_to_send_date = CAST(date_to_send AS DATE)
                    WHERE date_to_send_date IS NULL
                      AND date_to_send ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
                    """
                )
                c.execute("CREATE INDEX IF NOT EXISTS idx_daily_posts_date_to_send_date ON daily_posts (date_to_send_date)")

                conn.commit()
            except Exception as e:
                logger.warning("Migration Warning: %s", e)
                conn.rollback()
            finally:
                conn.close()

    # --- Explizite Spaltenauswahl ---
    def _get_model_columns(self):
        return """
            key, replicate_id, name, description, 
            base_cost_usd, internal_cost, custom_price, 
            provider, model_type, menu_path, is_active, is_favorite,
            is_commercial, manual_override, 
            input_schema, output_schema, example_data
        """

    def get_all_models(self) -> list[AIModel]:
        """
        Holt alle aktiven Modelle.
        Ergebnis wird für 60 Sekunden gecacht, um Neon zu entlasten.
        """
        # einfacher Cache ohne Lock – Lesen aus Attributen ist threadsafe genug,
        # DB-Zugriff selbst ist per self.lock geschützt.
        cache = getattr(self, "_models_cache", None)
        ts = getattr(self, "_models_cache_ts", 0)
        if cache is not None and (time.time() - ts) < 60:
            return cache

        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                query = (
                    f"SELECT {self._get_model_columns()} FROM ai_models "
                    "WHERE is_active = 1 "
                    "ORDER BY is_favorite DESC, menu_path, name"
                )
                c.execute(query)
                rows = c.fetchall()
                models = [self._map_row(r) for r in rows]
            finally:
                conn.close()

        self._models_cache = models
        self._models_cache_ts = time.time()
        return models

    def get_models_for_menu(self) -> list[AIModel]:
        """
        Lightweight Modell-Query für Menü/WebApp-Listen.
        Lässt schwere JSON-Schemas weg, behält aber example_data für Thumbnails.
        """
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT
                        key, replicate_id, name, description,
                        0.0 AS base_cost_usd, internal_cost, custom_price,
                        provider, model_type, menu_path, is_active, is_favorite,
                        is_commercial, manual_override,
                        '{}'::jsonb AS input_schema, '{}'::jsonb AS output_schema, example_data
                    FROM ai_models
                    WHERE is_active = 1
                    ORDER BY is_favorite DESC, menu_path, name
                    """
                )
                rows = c.fetchall()
                return [self._map_row(r) for r in rows]
            finally:
                conn.close()

    def get_model_by_key(self, key: str) -> AIModel:
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                query = f"SELECT {self._get_model_columns()} FROM ai_models WHERE key = %s"
                c.execute(query, (key,))
                r = c.fetchone()
                return self._map_row(r) if r else None
            finally:
                conn.close()

    def get_fallback_model(self, original_model: AIModel) -> AIModel:
        """Sucht Ersatzmodell."""
        main_type = original_model.type[0] if original_model.type else ""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            query = f"""
                SELECT {self._get_model_columns()} FROM ai_models 
                WHERE model_type LIKE %s 
                AND internal_cost <= %s 
                AND key != %s 
                AND is_active = 1
                LIMIT 1
            """
            c.execute(query, (f"%{main_type}%", original_model.internal_cost + 5, original_model.key))
            r = c.fetchone()
            return self._map_row(r) if r else None

    def _map_row(self, r):
        # Hilfsfunktion, um sicherzustellen, dass Schemas DICTs sind (egal ob JSONB oder Text)
        def ensure_dict(val):
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return {}
            return {}

        # 0:key, 1:rep_id, 2:name, 3:desc, 4:base_usd, 5:int_cost, 6:cust_price,
        # 7:prov, 8:type, 9:path, 10:active, 11:favorite, 12:comm, 13:override, 14:input, 15:output, 16:example
        
        return AIModel(
            key=r[0], 
            replicate_id=r[1], 
            name=r[2], 
            description=r[3] or "",
            base_cost_usd=r[4] or 0.0,
            internal_cost=r[5] or 10,
            custom_price=r[6],
            provider=r[7], 
            type=r[8].split(',') if r[8] else [],
            menu_path=r[9], 
            is_active=bool(r[10]),
            is_favorite=bool(r[11]),
            is_commercial=bool(r[12]),
            manual_override=bool(r[13]),
            # Hier nutzen wir die sichere Konvertierung
            input_schema=ensure_dict(r[14]),
            output_schema=ensure_dict(r[15]),
            example_data=ensure_dict(r[16])
        )

    # --- USER & SETTINGS METHODS ---
    def get_user_credits(self, user_id):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute("SELECT credits FROM users WHERE user_id = %s", (user_id,))
                res = c.fetchone()
                return res[0] if res else 0
            finally:
                conn.close()
            
    def update_credits(self, user_id, amount, reason="usage"):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                # User anlegen falls nicht existiert (mit Default 150 Credits)
                c.execute("INSERT INTO users (user_id, username) VALUES (%s, 'Unknown') ON CONFLICT (user_id) DO NOTHING", (user_id,))
                c.execute("UPDATE users SET credits = credits + %s WHERE user_id = %s", (amount, user_id))
                c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)", (user_id, amount, reason))
                conn.commit()
                # WARNING-Level: sichtbar in Railway/Cloud-Logs; wichtiger Audit-Trail
                logger.warning("TRANSACTION_RECORDED user_id=%s amount=%s reason=%s", user_id, amount, reason)
            except Exception as e:
                conn.rollback()
                logger.exception("update_credits FAILED user_id=%s amount=%s reason=%s: %s", user_id, amount, reason, e)
                raise
            finally:
                conn.close()

    def get_group_user_credits(self, user_id: int, chat_id: int) -> int:
        """Credits eines Users für eine bestimmte Gruppe (Kauf über Gruppen-Button)."""
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    "SELECT credits FROM group_user_credits WHERE user_id = %s AND chat_id = %s",
                    (user_id, chat_id)
                )
                res = c.fetchone()
                return res[0] if res else 0
            finally:
                conn.close()

    def update_group_user_credits(self, user_id: int, chat_id: int, amount: int, reason: str = "usage") -> None:
        """Credits für (user, group) hinzufügen. Nur für positive Beträge (Kauf)."""
        if amount <= 0:
            return
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO group_user_credits (user_id, chat_id, credits)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, chat_id) DO UPDATE SET credits = group_user_credits.credits + %s
            """, (user_id, chat_id, amount, amount))
            c.execute(
                "INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)",
                (user_id, amount, f"{reason}_grp_{chat_id}")
            )

    def get_effective_credits_for_group(self, user_id: int, chat_id: int) -> int:
        """Gesamt-Credits für Gruppen-Nutzung: Gruppen-Credits + User-Credits (Fallback)."""
        group_creds = self.get_group_user_credits(user_id, chat_id)
        user_creds = self.get_user_credits(user_id)
        return group_creds + user_creds

    def deduct_credits_for_group(self, user_id: int, chat_id: int, amount: int, reason: str = "usage") -> bool:
        """Zieht Credits ab: zuerst von Gruppen-Kontingent, Rest von User. Returns True wenn genug da war."""
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT credits FROM group_user_credits WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            row = c.fetchone()
            group_creds = row[0] if row else 0
            c.execute("SELECT credits FROM users WHERE user_id = %s", (user_id,))
            urow = c.fetchone()
            user_creds = urow[0] if urow else 0
            if group_creds + user_creds < amount:
                return False
            from_group = min(amount, group_creds)
            from_user = amount - from_group
            if from_group > 0:
                c.execute(
                    "UPDATE group_user_credits SET credits = credits - %s WHERE user_id = %s AND chat_id = %s",
                    (from_group, user_id, chat_id)
                )
                c.execute(
                    "INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)",
                    (user_id, -from_group, f"{reason}_grp_{chat_id}")
                )
                logger.warning("TRANSACTION_RECORDED (group) user_id=%s amount=%s reason=%s", user_id, -from_group, f"{reason}_grp_{chat_id}")
            if from_user > 0:
                c.execute("UPDATE users SET credits = credits - %s WHERE user_id = %s", (from_user, user_id))
                c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)", (user_id, -from_user, reason))
                logger.warning("TRANSACTION_RECORDED (user) user_id=%s amount=%s reason=%s", user_id, -from_user, reason)
            return True

    def get_user_settings(self, user_id):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    "SELECT language, auto_opt, auto_negative_prompt, daily_msg FROM users WHERE user_id = %s",
                    (user_id,),
                )
                result = c.fetchone()
            finally:
                conn.close()
            if result:
                lang = result[0] if result[0] and result[0].strip() in ("de", "en", "ru", "kk") else "en"
                return {
                    "lang": lang,
                    "auto_opt": bool(result[1]),
                    "auto_negative_prompt": bool(result[2]),
                    "daily_msg": bool(result[3]),
                }
            return {"lang": "en", "auto_opt": True, "auto_negative_prompt": True, "daily_msg": True}

    def add_user_if_not_exists(self, user_id, username):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, username))
                conn.commit()
            finally:
                conn.close()

    def update_setting(self, user_id, column, value):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                queries = {
                    "language": "UPDATE users SET language = %s WHERE user_id = %s",
                    "auto_opt": "UPDATE users SET auto_opt = %s WHERE user_id = %s",
                    "auto_negative_prompt": "UPDATE users SET auto_negative_prompt = %s WHERE user_id = %s",
                    "daily_msg": "UPDATE users SET daily_msg = %s WHERE user_id = %s",
                }
                q = queries.get(column)
                if q:
                    c.execute(q, (value, user_id))
                    conn.commit()
            finally:
                conn.close()

    def get_bot_setting(self, key: str, default: str = "") -> str:
        """Liest einen globalen Bot-Einstellungswert (z.B. menu_mode)."""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM bot_settings WHERE key = %s", (key,))
            res = c.fetchone()
            return res[0] if res else default

    def set_bot_setting(self, key: str, value: str) -> None:
        """Speichert eine globale Bot-Einstellung."""
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO bot_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
                (key, value, value)
            )

    def has_group_greeting_been_sent(self, user_id: int) -> bool:
        """Prüft ob dem User bereits die einmalige Willkommens-DM geschickt wurde."""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_sent (user_id BIGINT PRIMARY KEY)")
            c.execute("SELECT 1 FROM group_greeting_sent WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            return res is not None

    def has_group_greeting_been_attempted(self, user_id: int) -> bool:
        """Prüft ob wir bereits versucht haben, die Willkommens-DM zu senden (vermeidet erneute Gemini-Aufrufe)."""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_attempted (user_id BIGINT PRIMARY KEY)")
            c.execute("SELECT 1 FROM group_greeting_attempted WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            return res is not None

    def mark_group_greeting_sent(self, user_id: int) -> None:
        """Markiert dass dem User die einmalige Willkommens-DM geschickt wurde."""
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_sent (user_id BIGINT PRIMARY KEY)")
            c.execute("INSERT INTO group_greeting_sent (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))

    def mark_group_greeting_attempted(self, user_id: int) -> None:
        """Markiert dass wir versucht haben, die Willkommens-DM zu senden."""
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_attempted (user_id BIGINT PRIMARY KEY)")
            c.execute("INSERT INTO group_greeting_attempted (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))

    def add_group_if_not_exists(self, chat_id: int, lang: str = "en") -> None:
        """Fügt eine Gruppe hinzu, falls nicht vorhanden (für Random-Posts)."""
        if lang not in ("de", "en", "ru", "kk"):
            lang = "en"
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO group_settings (chat_id, language) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING",
                        (chat_id, lang)
                    )
            except Exception as e:
                logger.warning("add_group_if_not_exists failed: %s", e)

    def get_all_tracked_groups(self) -> list:
        """Alle bekannten Gruppen-Chat-IDs (group_settings)."""
        with self.lock:
            try:
                with self._connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT chat_id FROM group_settings")
                    rows = c.fetchall()
                    return [r[0] for r in rows] if rows else []
            except Exception:
                return []

    def get_azamat_random_count_today(self) -> int:
        """Anzahl heute bereits gesendeter Random-Posts."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.lock:
            try:
                with self._connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT count FROM azamat_random_count WHERE sent_date = %s", (today,))
                    row = c.fetchone()
                    return int(row[0]) if row and row[0] is not None else 0
            except Exception:
                return 0

    def increment_azamat_random_count_today(self) -> None:
        """Erhöht den Zähler für heute gesendete Random-Posts."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO azamat_random_count (sent_date, count) VALUES (%s, 1) "
                        "ON CONFLICT (sent_date) DO UPDATE SET count = azamat_random_count.count + 1",
                        (today,)
                    )
            except Exception as e:
                logger.warning("increment_azamat_random_count failed: %s", e)

    def get_group_language(self, chat_id: int) -> str:
        """Sprache für eine Gruppe. Default: en."""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_settings (chat_id BIGINT PRIMARY KEY, language TEXT DEFAULT 'en')")
            c.execute("SELECT language FROM group_settings WHERE chat_id = %s", (chat_id,))
            res = c.fetchone()
            lang = (res[0] or "en") if res else "en"
            return lang if lang in ("de", "en", "ru", "kk") else "en"

    def set_group_language(self, chat_id: int, lang: str) -> None:
        """Sprache für eine Gruppe setzen."""
        if lang not in ("de", "en", "ru", "kk"):
            return
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_settings (chat_id BIGINT PRIMARY KEY, language TEXT DEFAULT 'de')")
            c.execute(
                "INSERT INTO group_settings (chat_id, language) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET language = %s",
                (chat_id, lang, lang)
            )

    def set_user_chat_mode(self, user_id, model_key, active=True):
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            # Ohne users-Zeile schlägt UPDATE still fehl → Chat-Modus wirkt „kaputt“ (z. B. erste DM ohne /start).
            c.execute(
                "INSERT INTO users (user_id, username) VALUES (%s, 'Unknown') ON CONFLICT (user_id) DO NOTHING",
                (user_id,),
            )
            is_active = 1 if active else 0
            if model_key:
                c.execute(
                    "UPDATE users SET is_chat_mode = %s, last_model_key = %s WHERE user_id = %s",
                    (is_active, model_key, user_id),
                )
            else:
                c.execute("UPDATE users SET is_chat_mode = %s WHERE user_id = %s", (is_active, user_id))

    def get_user_chat_state(self, user_id):
        with self.lock:
            try:
                with self._connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT is_chat_mode, last_model_key FROM users WHERE user_id = %s", (user_id,))
                    res = c.fetchone()
                    if res:
                        return {"is_chat": bool(res[0]), "model_key": res[1]}
            except Exception:
                pass
            return {"is_chat": False, "model_key": None}

    def get_ai_news_rss_feed_urls(self) -> list[str]:
        """Aktive RSS-URLs für Daily AI News (Neon). Leer, wenn keine DB oder Tabelle fehlt."""
        if not self.db_url:
            return []
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            try:
                c.execute(
                    "SELECT feed_url FROM ai_news_rss_feeds WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
                )
                rows = c.fetchall()
                return [str(r[0]).strip() for r in rows if r and r[0] and str(r[0]).strip()]
            except Exception as e:
                logger.debug("get_ai_news_rss_feed_urls: %s", e)
                return []
            finally:
                conn.close()

    def user_exists(self, user_id):
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            return c.fetchone() is not None

    def get_user(self, user_id: int) -> User:
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, username, credits FROM users WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            if res:
                return User(id=res[0], username=res[1], credits=res[2])
            else:
                return User(id=user_id, username="Guest", credits=0)

    # --- DAILY SERVICE ---
    def get_due_daily_post(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT id, message_text, image_path
                    FROM daily_posts
                    WHERE (
                        date_to_send_date = %s::date
                        OR date_to_send = %s
                    ) AND sent_status = 0
                    """,
                    (today, today),
                )
                result = c.fetchone()
                return result
            finally:
                conn.close()

    def mark_post_as_sent(self, post_id):
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            c.execute("UPDATE daily_posts SET sent_status = 1 WHERE id = %s", (post_id,))

    def get_subscribed_users(self):
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE daily_msg = 1")
            results = c.fetchall()
            return [r[0] for r in results]

    def has_azamat_greeting_been_sent(self, user_id: int, sent_date: str, slot: int) -> bool:
        with self.lock:
            try:
                with self._connection() as conn:
                    c = conn.cursor()
                    c.execute(
                        "SELECT 1 FROM azamat_daily_sent WHERE user_id = %s AND sent_date = %s AND slot = %s",
                        (user_id, sent_date, slot)
                    )
                    return c.fetchone() is not None
            except Exception:
                return False

    def mark_azamat_greeting_sent(self, user_id: int, sent_date: str, slot: int) -> None:
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO azamat_daily_sent (user_id, sent_date, slot) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (user_id, sent_date, slot)
                    )
            except Exception as e:
                logger.warning("mark_azamat_greeting_sent failed: %s", e)

    def get_user_username_or_name(self, user_id: int) -> str:
        """Holt username oder user_id als Fallback für Begrüßungen."""
        with self.lock:
            try:
                with self._connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
                    row = c.fetchone()
                    return (row[0] or "User") if row else "User"
            except Exception:
                return "User"

    # --- GENERATION ERRORS (Logging + 7-Tage-Cleanup) ---
    def insert_generation_error(self, user_id: int, model_key: str, error_message: str):
        """Speichert Fehlermeldung zu einem fehlgeschlagenen Generierungsversuch."""
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO generation_errors (user_id, model_key, error_message) VALUES (%s, %s, %s)",
                        (user_id, model_key or "", (error_message or "")[:2000])
                    )
            except Exception as e:
                logger.warning("Fehler beim Speichern von generation_error: %s", e)

    def cleanup_old_generation_errors(self):
        """Löscht Einträge älter als 7 Tage."""
        with self.lock:
            try:
                with self._connection(commit=True) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM generation_errors WHERE created_at < NOW() - INTERVAL '7 days'")
                    deleted = c.rowcount
                if deleted:
                    logger.info("generation_errors cleanup: %s Einträge älter als 7 Tage gelöscht.", deleted)
            except Exception as e:
                logger.warning("generation_errors Cleanup failed: %s", e)

    def insert_replicate_webhook_job(
        self,
        prediction_id: str,
        user_id: int,
        model_key: str,
        lang: str,
        effective_cost: int,
        *,
        no_charge: bool = False,
        group_chat_id: int | None = None,
        is_chat: bool = False,
        chat_history_mode: str | None = None,
        user_prompt: str | None = None,
    ) -> None:
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO replicate_webhook_jobs (
                        prediction_id, user_id, model_key, lang, effective_cost,
                        no_charge, group_chat_id, is_chat, chat_history_mode, user_prompt
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        prediction_id,
                        user_id,
                        model_key,
                        lang,
                        effective_cost,
                        1 if no_charge else 0,
                        group_chat_id,
                        1 if is_chat else 0,
                        chat_history_mode,
                        (user_prompt or "")[:4000] if user_prompt else None,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def fetch_replicate_webhook_job(self, prediction_id: str) -> dict | None:
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT prediction_id, user_id, model_key, lang, effective_cost,
                           no_charge, group_chat_id, is_chat, chat_history_mode, user_prompt
                    FROM replicate_webhook_jobs WHERE prediction_id = %s
                    """,
                    (prediction_id,),
                )
                row = c.fetchone()
                if not row:
                    return None
                return {
                    "prediction_id": row[0],
                    "user_id": int(row[1]),
                    "model_key": row[2],
                    "lang": row[3] or "en",
                    "effective_cost": int(row[4]),
                    "no_charge": bool(row[5]),
                    "group_chat_id": int(row[6]) if row[6] is not None else None,
                    "is_chat": bool(row[7]),
                    "chat_history_mode": row[8],
                    "user_prompt": row[9] or "",
                }
            finally:
                conn.close()

    def delete_replicate_webhook_job(self, prediction_id: str) -> None:
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute("DELETE FROM replicate_webhook_jobs WHERE prediction_id = %s", (prediction_id,))
                conn.commit()
            finally:
                conn.close()

    # --- CHAT SESSIONS (eine Zeile pro User+Modell) ---

    def _ensure_chat_sessions_table(self, cursor) -> None:
        """Stellt sicher, dass die Tabelle chat_sessions existiert (idempotent)."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                user_id    BIGINT NOT NULL,
                model_key  TEXT   NOT NULL,
                history    TEXT   NOT NULL,
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (user_id, model_key)
            );
            """
        )

    def get_chat_session(self, user_id: int, model_key: str) -> list[dict]:
        """Gibt History als Liste von {role, content} zurück."""
        with self.lock, self._connection() as conn:
            c = conn.cursor()
            self._ensure_chat_sessions_table(c)
            conn.commit()
            c.execute(
                "SELECT history FROM chat_sessions WHERE user_id = %s AND model_key = %s",
                (user_id, model_key),
            )
            row = c.fetchone()
        if not row or not row[0]:
            return []
        try:
            return json.loads(row[0])
        except Exception:
            return []

    def save_chat_session(self, user_id: int, model_key: str, messages: list[dict]) -> None:
        """Speichert History als JSON (UPSERT)."""
        payload = json.dumps(messages, ensure_ascii=False)
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            self._ensure_chat_sessions_table(c)
            c.execute(
                """
                INSERT INTO chat_sessions (user_id, model_key, history, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, model_key)
                DO UPDATE SET history = EXCLUDED.history, updated_at = NOW()
                """,
                (user_id, model_key, payload),
            )

    def clear_chat_session(self, user_id: int, model_key: str | None = None) -> None:
        """Löscht den Chat-Verlauf eines Users (optional nur für ein Modell)."""
        with self.lock, self._connection(commit=True) as conn:
            c = conn.cursor()
            self._ensure_chat_sessions_table(c)
            if model_key:
                c.execute(
                    "DELETE FROM chat_sessions WHERE user_id = %s AND model_key = %s",
                    (user_id, model_key),
                )
            else:
                c.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))

    # --- Telegram-Kanäle (Tabelle telegram_channels, gleiche DB wie DATABASE_URL) ---

    def upsert_telegram_channel(
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
        """touch_receive_daily_news=False: receive_daily_news bleibt bei ON CONFLICT unverändert."""
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
                logger.warning("upsert_telegram_channel failed: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()

    def set_telegram_channel_receive_daily_news(self, chat_id: int, enabled: bool = True) -> None:
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
                logger.warning("set_telegram_channel_receive_daily_news failed: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()

    def should_skip_channel_from_group_daily(self, chat_id: int) -> bool:
        """True: als Channel erfasst → nicht über den normalen Gruppen-Daily-Loop."""
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
                logger.warning("should_skip_channel_from_group_daily failed: %s", e)
                return False
            finally:
                conn.close()

    def iter_telegram_channels_daily_news(self) -> list[tuple[int, str]]:
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
                logger.warning("iter_telegram_channels_daily_news failed: %s", e)
                return []
            finally:
                conn.close()

    def list_telegram_channels(self) -> list[dict]:
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
                out: list[dict] = []
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
                logger.warning("list_telegram_channels failed: %s", e)
                return []
            finally:
                conn.close()

    def get_telegram_channel_row(self, chat_id: int) -> dict | None:
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
                logger.warning("get_telegram_channel_row failed: %s", e)
                return None
            finally:
                conn.close()