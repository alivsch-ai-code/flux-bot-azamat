import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def transfer_approved():
    db_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()

    print("🚀 Übertrage freigegebene Entities in Produktion...")
    
    # Transfer-SQL berücksichtigt alle Felder der dataclass AIModel
    transfer_sql = """
    INSERT INTO ai_models (
        key, replicate_id, name, description, base_cost_usd, 
        internal_cost, custom_price, provider, model_type, 
        menu_path, is_active, is_commercial, input_schema, 
        output_schema, example_data
    )
    SELECT 
        key, replicate_id, name, description, base_cost_usd, 
        internal_cost, custom_price, provider, model_type, 
        menu_path, 1, is_commercial, input_schema, 
        output_schema, example_data
    FROM ai_models_staging
    WHERE is_approved = 1
    ON CONFLICT (key) DO UPDATE SET
        base_cost_usd = EXCLUDED.base_cost_usd,
        internal_cost = EXCLUDED.internal_cost,
        input_schema = EXCLUDED.input_schema,
        output_schema = EXCLUDED.output_schema,
        example_data = EXCLUDED.example_data,
        last_checked = NOW();
    """

    cur.execute(transfer_sql)
    count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {count} Modelle erfolgreich live geschaltet.")

if __name__ == "__main__":
    transfer_approved()