"""
Smart-Import: Lädt Modelle aus Replicate (Collections + Suche) ins Staging.
Nutzt replicate_fetcher für einheitliche Metadaten.
Bestehende manuelle Änderungen (manual_override=1) werden beibehalten.
"""
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

import replicate

from src.tools.replicate_fetcher import model_to_row

load_dotenv()

# Priorität für Smart-Import (werden zuerst geladen)
PRIORITY_MODELS = [
    "black-forest-labs/flux-1.1-pro",
    "black-forest-labs/flux-schnell",
    "black-forest-labs/flux-1.1-pro-ultra",
    "tencent/hunyuan-video",
    "kwaivgi/kling-v1.6-pro",
    "google/gemini-2.5-flash",
    "openai/gpt-5-nano",
    "meta/meta-llama-3.1-405b-instruct",
    "deepseek-ai/deepseek-r1",
    "nightmareai/real-esrgan",
    "lucataco/remove-bg",
]

TARGET_COLLECTIONS = ["official", "image-generation", "video-generation"]
TARGET_PROVIDERS = [
    "google", "kwaivgi", "wan-video", "tencent", "black-forest-labs",
    "meta", "mistralai", "wavespeedai",
]
TARGET_KEYWORDS = ["gemini", "kling", "wan", "flux", "llama", "video", "chat", "upscale"]


def ensure_staging_exists(cur):
    cur.execute("""
        SELECT EXISTS (SELECT 1 FROM information_schema.tables
        WHERE table_name = 'ai_models_staging');
    """)
    if not cur.fetchone()[0]:
        raise RuntimeError(
            "ai_models_staging fehlt. Führe zuerst: python -m src.tools.init"
        )


def run_import():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL fehlt!")
        return

    conn = psycopg2.connect(db_url, sslmode="require")
    cur = conn.cursor()
    ensure_staging_exists(cur)

    print("📥 Starte Smart-Import (manuelle Edits bleiben erhalten)...")
    models_to_process = {}

    # 1. Collections
    for slug in TARGET_COLLECTIONS:
        try:
            col = replicate.collections.get(slug)
            if col:
                for m in col.models:
                    full_id = f"{m.owner}/{m.name}"
                    models_to_process[full_id] = m
        except Exception:
            pass

    # 2. Suche
    for query in TARGET_PROVIDERS + TARGET_KEYWORDS:
        try:
            for m in replicate.models.search(query):
                full_id = f"{m.owner}/{m.name}"
                if m.owner in TARGET_PROVIDERS or any(k in m.name.lower() for k in TARGET_KEYWORDS):
                    models_to_process[full_id] = m
        except Exception:
            continue

    # 3. Priority
    for mid in PRIORITY_MODELS:
        if mid not in models_to_process:
            try:
                models_to_process[mid] = replicate.models.get(mid)
            except Exception:
                print(f"   ❌ Priority {mid} nicht gefunden.")

    print(f"📦 Verarbeite {len(models_to_process)} Modelle...")
    ok, skip = 0, 0

    for full_id, model in models_to_process.items():
        try:
            row = model_to_row(model, full_id)
            if not row:
                skip += 1
                continue

            cur.execute("""
                INSERT INTO ai_models_staging (
                    key, replicate_id, name, description, base_cost_usd, internal_cost,
                    provider, model_type, menu_path, input_schema, output_schema, example_data,
                    is_approved, manual_override
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0)
                ON CONFLICT (key) DO UPDATE SET
                    replicate_id = EXCLUDED.replicate_id,
                    base_cost_usd = EXCLUDED.base_cost_usd,
                    input_schema = EXCLUDED.input_schema,
                    output_schema = EXCLUDED.output_schema,
                    example_data = EXCLUDED.example_data,
                    last_checked = NOW(),
                    name = CASE WHEN ai_models_staging.manual_override = 1
                        THEN ai_models_staging.name ELSE EXCLUDED.name END,
                    description = CASE WHEN ai_models_staging.manual_override = 1
                        THEN ai_models_staging.description ELSE EXCLUDED.description END,
                    internal_cost = CASE WHEN ai_models_staging.manual_override = 1
                        THEN ai_models_staging.internal_cost ELSE EXCLUDED.internal_cost END,
                    model_type = CASE WHEN ai_models_staging.manual_override = 1
                        THEN ai_models_staging.model_type ELSE EXCLUDED.model_type END,
                    menu_path = CASE WHEN ai_models_staging.manual_override = 1
                        THEN ai_models_staging.menu_path ELSE EXCLUDED.menu_path END;
            """, (
                row["key"],
                row["replicate_id"],
                row["name"],
                row["description"],
                row["base_cost_usd"],
                row["internal_cost"],
                row["provider"],
                row["model_type"],
                row["menu_path"],
                Json(row["input_schema"]),
                Json(row["output_schema"]),
                Json(row["example_data"]),
            ))
            conn.commit()
            ok += 1
            if ok % 20 == 0:
                print(f"   ... {ok} verarbeitet")
        except Exception as e:
            conn.rollback()
            print(f"   ❌ {full_id}: {e}")
            skip += 1

    cur.close()
    conn.close()
    print(f"✅ Fertig: {ok} Modelle aktualisiert, {skip} übersprungen.")
    print("   👉 Nutze Admin-GUI oder approve_to_main um freizugeben.")


if __name__ == "__main__":
    run_import()
