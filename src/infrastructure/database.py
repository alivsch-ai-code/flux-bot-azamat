import sqlite3
import threading
import os

class DatabaseManager:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Tabelle für User
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    credits INTEGER DEFAULT 50  -- Startguthaben (z.B. 50 Credits = 0.50€)
                )
            ''')
            # Tabelle für Transaktionen
            c.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()

    def get_user_credits(self, user_id):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            # Falls User nicht existiert, gibt er 0 zurück (oder man legt ihn hier an)
            return result[0] if result else 0

    def add_user_if_not_exists(self, user_id, username):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            conn.commit()
            conn.close()

    def update_credits(self, user_id, amount, reason="usage"):
        """
        amount kann positiv (Aufladung) oder negativ (Verbrauch) sein.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # User sicherstellen
            c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            # Guthaben ändern
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
            # Transaktion loggen
            c.execute("INSERT INTO transactions (user_id, amount, reason) VALUES (?, ?, ?)", (user_id, amount, reason))
            conn.commit()
            conn.close()