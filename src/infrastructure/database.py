import psycopg2
import threading
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from src.domain.entities import User, AIModel

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.lock = threading.Lock()
        
        if self.db_url:
            self._init_db()
            self._migrate_db()
        else:
            print("⚠️ DATABASE_URL fehlt in .env")

    def _get_connection(self):
        return psycopg2.connect(self.db_url, sslmode='require')

    def _init_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                
                # Users Tabelle
                c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        credits INTEGER DEFAULT 150,
                        language TEXT DEFAULT 'de',
                        auto_opt INTEGER DEFAULT 1,
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
                # Gruppen-spezifische Credits pro User (Kauf über Gruppen-Button)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS group_user_credits (
                        user_id BIGINT NOT NULL,
                        chat_id BIGINT NOT NULL,
                        credits INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, chat_id)
                    )
                ''')
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"❌ DB Init Error: {e}")

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
                    ("is_chat_mode", "INTEGER DEFAULT 0")
                ]
                for col, dtype in user_cols:
                    c.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {dtype}")

                # 3. Bot-Settings Default: menu_mode
                c.execute("SELECT 1 FROM bot_settings WHERE key = 'menu_mode'")
                if c.fetchone() is None:
                    c.execute("INSERT INTO bot_settings (key, value) VALUES ('menu_mode', 'commands')")

                # 4. Gruppen-Einstellungen
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

                conn.commit()
            except Exception as e:
                print(f"⚠️ Migration Warning: {e}")
                conn.rollback()
            finally:
                conn.close()

    # --- Explizite Spaltenauswahl ---
    def _get_model_columns(self):
        return """
            key, replicate_id, name, description, 
            base_cost_usd, internal_cost, custom_price, 
            provider, model_type, menu_path, is_active, 
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
            c = conn.cursor()
            query = f"SELECT {self._get_model_columns()} FROM ai_models WHERE is_active = 1 ORDER BY menu_path, name"
            c.execute(query)
            rows = c.fetchall()
            conn.close()
            models = [self._map_row(r) for r in rows]

        self._models_cache = models
        self._models_cache_ts = time.time()
        return models

    def get_model_by_key(self, key: str) -> AIModel:
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            query = f"SELECT {self._get_model_columns()} FROM ai_models WHERE key = %s"
            c.execute(query, (key,))
            r = c.fetchone()
            conn.close()
            return self._map_row(r) if r else None

    def get_fallback_model(self, original_model: AIModel) -> AIModel:
        """Sucht Ersatzmodell."""
        main_type = original_model.type[0] if original_model.type else ""
        with self.lock:
            conn = self._get_connection()
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
            conn.close()
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
        # 7:prov, 8:type, 9:path, 10:active, 11:comm, 12:override, 13:input, 14:output, 15:example
        
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
            is_commercial=bool(r[11]),
            manual_override=bool(r[12]),
            # Hier nutzen wir die sichere Konvertierung
            input_schema=ensure_dict(r[13]),
            output_schema=ensure_dict(r[14]),
            example_data=ensure_dict(r[15])
        )

    # --- USER & SETTINGS METHODS ---
    def get_user_credits(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            conn.close()
            return res[0] if res else 0
            
    def update_credits(self, user_id, amount, reason="usage"):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            # User anlegen falls nicht existiert (mit Default 150 Credits)
            c.execute("INSERT INTO users (user_id, username) VALUES (%s, 'Unknown') ON CONFLICT (user_id) DO NOTHING", (user_id,))
            c.execute("UPDATE users SET credits = credits + %s WHERE user_id = %s", (amount, user_id))
            c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)", (user_id, amount, reason))
            conn.commit()
            conn.close()

    def get_group_user_credits(self, user_id: int, chat_id: int) -> int:
        """Credits eines Users für eine bestimmte Gruppe (Kauf über Gruppen-Button)."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                "SELECT credits FROM group_user_credits WHERE user_id = %s AND chat_id = %s",
                (user_id, chat_id)
            )
            res = c.fetchone()
            conn.close()
            return res[0] if res else 0

    def update_group_user_credits(self, user_id: int, chat_id: int, amount: int, reason: str = "usage") -> None:
        """Credits für (user, group) hinzufügen. Nur für positive Beträge (Kauf)."""
        if amount <= 0:
            return
        with self.lock:
            conn = self._get_connection()
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
            conn.commit()
            conn.close()

    def get_effective_credits_for_group(self, user_id: int, chat_id: int) -> int:
        """Gesamt-Credits für Gruppen-Nutzung: Gruppen-Credits + User-Credits (Fallback)."""
        group_creds = self.get_group_user_credits(user_id, chat_id)
        user_creds = self.get_user_credits(user_id)
        return group_creds + user_creds

    def deduct_credits_for_group(self, user_id: int, chat_id: int, amount: int, reason: str = "usage") -> bool:
        """Zieht Credits ab: zuerst von Gruppen-Kontingent, Rest von User. Returns True wenn genug da war."""
        with self.lock:
            conn = self._get_connection()
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
                conn.close()
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
            if from_user > 0:
                c.execute("UPDATE users SET credits = credits - %s WHERE user_id = %s", (from_user, user_id))
                c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)", (user_id, -from_user, reason))
            conn.commit()
            conn.close()
            return True

    def get_user_settings(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT language, auto_opt, daily_msg FROM users WHERE user_id = %s", (user_id,))
            result = c.fetchone()
            conn.close()
            if result:
                lang = result[0] if result[0] and result[0].strip() else 'de'
                return {"lang": lang, "auto_opt": bool(result[1]), "daily_msg": bool(result[2])}
            return {"lang": "de", "auto_opt": True, "daily_msg": True}

    def add_user_if_not_exists(self, user_id, username):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, username))
            conn.commit()
            conn.close()

    def update_setting(self, user_id, column, value):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            if column in ["language", "auto_opt", "daily_msg"]:
                c.execute(f"UPDATE users SET {column} = %s WHERE user_id = %s", (value, user_id))
                conn.commit()
            conn.close()

    def get_bot_setting(self, key: str, default: str = "") -> str:
        """Liest einen globalen Bot-Einstellungswert (z.B. menu_mode)."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT value FROM bot_settings WHERE key = %s", (key,))
            res = c.fetchone()
            conn.close()
            return res[0] if res else default

    def set_bot_setting(self, key: str, value: str) -> None:
        """Speichert eine globale Bot-Einstellung."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT INTO bot_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s",
                (key, value, value)
            )
            conn.commit()
            conn.close()

    def has_group_greeting_been_sent(self, user_id: int) -> bool:
        """Prüft ob dem User bereits die einmalige Willkommens-DM geschickt wurde."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_sent (user_id BIGINT PRIMARY KEY)")
            c.execute("SELECT 1 FROM group_greeting_sent WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            conn.close()
            return res is not None

    def has_group_greeting_been_attempted(self, user_id: int) -> bool:
        """Prüft ob wir bereits versucht haben, die Willkommens-DM zu senden."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_attempted (user_id BIGINT PRIMARY KEY)")
            c.execute("SELECT 1 FROM group_greeting_attempted WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            conn.close()
            return res is not None

    def mark_group_greeting_sent(self, user_id: int) -> None:
        """Markiert dass dem User die einmalige Willkommens-DM geschickt wurde."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_sent (user_id BIGINT PRIMARY KEY)")
            c.execute("INSERT INTO group_greeting_sent (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
            conn.commit()
            conn.close()

    def mark_group_greeting_attempted(self, user_id: int) -> None:
        """Markiert dass wir versucht haben, die Willkommens-DM zu senden."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_greeting_attempted (user_id BIGINT PRIMARY KEY)")
            c.execute("INSERT INTO group_greeting_attempted (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
            conn.commit()
            conn.close()

    def get_group_language(self, chat_id: int) -> str:
        """Sprache für eine Gruppe. Default: de."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_settings (chat_id BIGINT PRIMARY KEY, language TEXT DEFAULT 'de')")
            c.execute("SELECT language FROM group_settings WHERE chat_id = %s", (chat_id,))
            res = c.fetchone()
            conn.close()
            return (res[0] or "de") if res else "de"

    def set_group_language(self, chat_id: int, lang: str) -> None:
        """Sprache für eine Gruppe setzen."""
        if lang not in ("de", "en", "ru", "kk"):
            return
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS group_settings (chat_id BIGINT PRIMARY KEY, language TEXT DEFAULT 'de')")
            c.execute(
                "INSERT INTO group_settings (chat_id, language) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET language = %s",
                (chat_id, lang, lang)
            )
            conn.commit()
            conn.close()

    def set_user_chat_mode(self, user_id, model_key, active=True):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            is_active = 1 if active else 0
            if model_key:
                c.execute("UPDATE users SET is_chat_mode = %s, last_model_key = %s WHERE user_id = %s", (is_active, model_key, user_id))
            else:
                c.execute("UPDATE users SET is_chat_mode = %s WHERE user_id = %s", (is_active, user_id))
            conn.commit()
            conn.close()

    def get_user_chat_state(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            try:
                c.execute("SELECT is_chat_mode, last_model_key FROM users WHERE user_id = %s", (user_id,))
                res = c.fetchone()
                conn.close()
                if res:
                    return {"is_chat": bool(res[0]), "model_key": res[1]}
            except Exception:
                conn.rollback()
                conn.close()
            return {"is_chat": False, "model_key": None}
            
    def user_exists(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            exists = c.fetchone() is not None
            conn.close()
            return exists

    def get_user(self, user_id: int) -> User:
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT user_id, username, credits FROM users WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            conn.close()
            if res:
                return User(id=res[0], username=res[1], credits=res[2])
            else:
                return User(id=user_id, username="Guest", credits=0)

    # --- DAILY SERVICE ---
    def get_due_daily_post(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT id, message_text, image_path FROM daily_posts WHERE date_to_send = %s AND sent_status = 0", (today,))
            result = c.fetchone()
            conn.close()
            return result 

    def mark_post_as_sent(self, post_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("UPDATE daily_posts SET sent_status = 1 WHERE id = %s", (post_id,))
            conn.commit()
            conn.close()

    def get_subscribed_users(self):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE daily_msg = 1")
            results = c.fetchall()
            conn.close()
            return [r[0] for r in results]

    def has_azamat_greeting_been_sent(self, user_id: int, sent_date: str, slot: int) -> bool:
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                c.execute(
                    "SELECT 1 FROM azamat_daily_sent WHERE user_id = %s AND sent_date = %s AND slot = %s",
                    (user_id, sent_date, slot)
                )
                res = c.fetchone()
                conn.close()
                return res is not None
            except Exception:
                return False

    def mark_azamat_greeting_sent(self, user_id: int, sent_date: str, slot: int) -> None:
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO azamat_daily_sent (user_id, sent_date, slot) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (user_id, sent_date, slot)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ mark_azamat_greeting_sent: {e}")

    def get_user_username_or_name(self, user_id: int) -> str:
        """Holt username oder user_id als Fallback für Begrüßungen."""
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                c.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
                row = c.fetchone()
                conn.close()
                return (row[0] or f"User") if row else "User"
            except Exception:
                return "User"

    # --- GENERATION ERRORS (Logging + 7-Tage-Cleanup) ---
    def insert_generation_error(self, user_id: int, model_key: str, error_message: str):
        """Speichert Fehlermeldung zu einem fehlgeschlagenen Generierungsversuch."""
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO generation_errors (user_id, model_key, error_message) VALUES (%s, %s, %s)",
                    (user_id, model_key or "", (error_message or "")[:2000])
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ Fehler beim Speichern von generation_error: {e}")

    def cleanup_old_generation_errors(self):
        """Löscht Einträge älter als 7 Tage."""
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM generation_errors WHERE created_at < NOW() - INTERVAL '7 days'")
                deleted = c.rowcount
                conn.commit()
                conn.close()
                if deleted:
                    print(f"🧹 generation_errors: {deleted} Einträge älter als 7 Tage gelöscht.")
            except Exception as e:
                print(f"⚠️ generation_errors Cleanup: {e}")

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
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            self._ensure_chat_sessions_table(c)
            conn.commit()
            c.execute(
                "SELECT history FROM chat_sessions WHERE user_id = %s AND model_key = %s",
                (user_id, model_key),
            )
            row = c.fetchone()
            conn.close()
        if not row or not row[0]:
            return []
        try:
            return json.loads(row[0])
        except Exception:
            return []

    def save_chat_session(self, user_id: int, model_key: str, messages: list[dict]) -> None:
        """Speichert History als JSON (UPSERT)."""
        payload = json.dumps(messages, ensure_ascii=False)
        with self.lock:
            conn = self._get_connection()
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
            conn.commit()
            conn.close()

    def clear_chat_session(self, user_id: int, model_key: str | None = None) -> None:
        """Löscht den Chat-Verlauf eines Users (optional nur für ein Modell)."""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            self._ensure_chat_sessions_table(c)
            if model_key:
                c.execute(
                    "DELETE FROM chat_sessions WHERE user_id = %s AND model_key = %s",
                    (user_id, model_key),
                )
            else:
                c.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))
            conn.commit()
            conn.close()