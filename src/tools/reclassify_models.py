"""
Reclassify-Models: Wendet die verbesserte Klassifikationslogik auf bestehende Modelle an.

Korrigiert model_type und menu_path basierend auf Input- und Output-Schema.
Nützlich nach Änderungen an replicate_fetcher.infer_model_type.

Verwendung:
  python -m src.tools.reclassify_models          # Staging-Tabelle
  python -m src.tools.reclassify_models --main   # Haupt-Tabelle ai_models
"""
import argparse
import json
import os

from src.tools.replicate_fetcher import infer_model_type

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def reclassify_from_schema(input_schema: dict, output_schema: dict, name: str, description: str = "", model_key: str = ""):
    """Berechnet model_type und menu_path aus Schemas."""
    return infer_model_type(
        name, description or "",
        input_schema=input_schema, output_schema=output_schema, model_key=model_key or "",
    )


def run_on_db(table: str = "ai_models_staging"):
    """Aktualisiert model_type und menu_path in der DB."""
    import psycopg2
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL fehlt in .env")
        return

    conn = psycopg2.connect(db_url, sslmode="require")
    cur = conn.cursor()
    cur.execute(f"SELECT key, name, description, input_schema, output_schema, model_type, menu_path FROM {table}")
    rows = cur.fetchall()
    updated = 0
    for row in rows:
        key, name, desc, inp, out, old_type, old_path = row
        inp = inp or {}
        out = out or {}
        if isinstance(inp, str):
            try:
                inp = json.loads(inp)
            except Exception:
                inp = {}
        if isinstance(out, str):
            try:
                out = json.loads(out)
            except Exception:
                out = {}
        new_type, new_path = reclassify_from_schema(inp, out, name or key, desc or "", model_key=key)
        if new_type != (old_type or "") or new_path != (old_path or ""):
            cur.execute(
                f"UPDATE {table} SET model_type = %s, menu_path = %s WHERE key = %s",
                (new_type, new_path, key),
            )
            print(f"  OK {key}: {old_type or '?'} -> {new_type}, {old_path or '?'} -> {new_path}")
            updated += 1
    conn.commit()
    cur.close()
    conn.close()
    print(f"\n{updated} models updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", action="store_true", help="Haupt-Tabelle ai_models statt Staging")
    args = parser.parse_args()

    table = "ai_models" if args.main else "ai_models_staging"
    print(f"Reclassifying models in {table}...")
    run_on_db(table)
