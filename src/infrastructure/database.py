import psycopg2
import threading
import os
from datetime import datetime
# NEU: Damit werden Variablen aus der .env Datei geladen
from dotenv import load_dotenv

from src.domain.entities import User

# Lädt Umgebungsvariablen aus .env (nur lokal relevant, auf Render passiert nichts)
load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Holt URL aus .env (lokal) oder Render Environment (server)
        self.db_url = os.getenv("DATABASE_URL")
        
        if not self.db_url:
            print("⚠️ ACHTUNG: DATABASE_URL nicht gefunden! Stelle sicher, dass sie in der .env steht.")
            
        self.lock = threading.Lock()
        # Wir rufen init nur auf, wenn wir eine URL haben, sonst kracht es
        if self.db_url:
            self._init_db()
            self._migrate_db()

    def _get_connection(self):
        """Erstellt eine neue Verbindung zur Datenbank."""
        return psycopg2.connect(self.db_url, sslmode='require')

    def _init_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                
                c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        credits INTEGER DEFAULT 150,
                        language TEXT DEFAULT 'de',
                        auto_opt INTEGER DEFAULT 1,
                        daily_msg INTEGER DEFAULT 1
                    )
                ''')
                
                c.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        amount INTEGER,
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                c.execute('''
                    CREATE TABLE IF NOT EXISTS daily_posts (
                        id SERIAL PRIMARY KEY,
                        date_to_send TEXT UNIQUE, 
                        message_text TEXT,
                        image_path TEXT,
                        sent_status INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"❌ DB Init Error: {e}")

    def _migrate_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                c = conn.cursor()
                
                try:
                    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'de'")
                except: conn.rollback()
                else: conn.commit()

                try:
                    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_opt INTEGER DEFAULT 1")
                except: conn.rollback()
                else: conn.commit()
                
                try:
                    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_msg INTEGER DEFAULT 1")
                except: conn.rollback()
                else: conn.commit()
                
                conn.close()
            except Exception as e:
                print(f"Migration Error: {e}")

    # --- USER SETTINGS ---
    def get_user_settings(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT language, auto_opt, daily_msg FROM users WHERE user_id = %s", (user_id,))
            result = c.fetchone()
            conn.close()
            if result:
                return {
                    "lang": result[0], 
                    "auto_opt": bool(result[1]), 
                    "daily_msg": bool(result[2])
                }
            return {"lang": "de", "auto_opt": True, "daily_msg": True}

    def update_setting(self, user_id, column, value):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            if column not in ["language", "auto_opt", "daily_msg"]: return
            
            query = f"UPDATE users SET {column} = %s WHERE user_id = %s"
            c.execute(query, (value, user_id))
            conn.commit()
            conn.close()

    # --- DAILY MESSAGES ---
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
            
    # --- STANDARD METHODEN ---
    def user_exists(self, user_id):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            conn.close()
            return res is not None

    def add_user_if_not_exists(self, user_id, username):
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, username))
            conn.commit()
            conn.close()

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
            c.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
            c.execute("UPDATE users SET credits = credits + %s WHERE user_id = %s", (amount, user_id))
            c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (%s, %s, %s)", (user_id, amount, reason))
            conn.commit()
            conn.close()
            
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
                return User(id=user_id, username="Guest", credits=150)