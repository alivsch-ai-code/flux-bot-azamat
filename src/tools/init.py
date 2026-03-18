import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Fehler: DATABASE_URL nicht gefunden.")
        return

    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()

    # Tabellen für sauberen Neustart löschen
    tables = ["ai_models", "ai_models_staging"]
    print("🧹 Bereinige Datenbank (Drop outdated tables)...")
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

    # Schema-Basis basierend auf AIModel Entity (entities.py)
    # WICHTIG: Hier wurde 'manual_override' hinzugefügt!
    schema_fields = """
        key TEXT PRIMARY KEY,
        replicate_id TEXT NOT NULL,
        name TEXT,
        description TEXT,
        
        -- PREISE
        base_cost_usd FLOAT DEFAULT 0.0,
        internal_cost INTEGER DEFAULT 10,
        custom_price INTEGER,
        
        -- METADATA
        provider TEXT DEFAULT 'replicate',
        model_type TEXT, 
        menu_path TEXT DEFAULT 'root',
        is_active INTEGER DEFAULT 1,
        is_commercial INTEGER DEFAULT 1,
        manual_override INTEGER DEFAULT 0, -- <--- DIESE ZEILE HAT GEFEHLT
        
        -- JSON
        input_schema JSONB,
        output_schema JSONB,
        example_data JSONB,
        
        last_checked TIMESTAMP DEFAULT NOW()
    """

    print("🏗 Erstelle Tabellen mit neuem Schema...")
    cur.execute(f"CREATE TABLE ai_models ({schema_fields});")
    # Staging erhält zusätzlich die Approval-Spalte
    cur.execute(f"CREATE TABLE ai_models_staging ({schema_fields}, is_approved INTEGER DEFAULT 0);")

    # Persistenter Chat-Verlauf (optional, wird nicht gedroppt)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            model_key TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_messages_user_model_created
        ON chat_messages (user_id, model_key, created_at);
        """
    )

    # Neu: Session-basierter Verlauf (eine Zeile pro User+Modell mit JSON-History)
    cur.execute(
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
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Datenbank erfolgreich initialisiert (inkl. manual_override).")

if __name__ == "__main__":
    setup_database()