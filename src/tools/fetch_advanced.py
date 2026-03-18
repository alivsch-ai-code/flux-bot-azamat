"""
Holt die kuratierte Best-of-Liste von Replicate-Modellen und schreibt sie ins Staging.
Pro Kategorie (Image, Video, Audio, Text) die besten verfügbaren Modelle.
- Image: Flux Pro/Ultra, Schnell, Fill, Tools (Upscale, Remove-BG)
- Video: Kling, Hunyuan, Veo
- Audio: Bark, MusicGen, Whisper
- Text: Gemini, GPT-5-Nano, Claude, Llama, DeepSeek
"""
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

import replicate

from src.tools.replicate_fetcher import model_to_row

load_dotenv()

# Kuratierte Best-of pro Kategorie – erweiterte Liste
DEFAULT_BEST_MODELS = [
    # --- IMAGE: Flux, Alternativen, Tools ---
    "black-forest-labs/flux-1.1-pro-ultra",
    "black-forest-labs/flux-1.1-pro",
    "black-forest-labs/flux-2-pro",
    "black-forest-labs/flux-2-flex",
    "black-forest-labs/flux-schnell",
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-fill-pro",
    "black-forest-labs/flux-depth-pro",
    "black-forest-labs/flux-canny-pro",
    "black-forest-labs/flux-redux-dev",
    "black-forest-labs/flux-kontext-pro",
    "black-forest-labs/flux-kontext-max",
    "lucataco/remove-bg",
    "nightmareai/real-esrgan",
    "stability-ai/sdxl",
    "ideogram-ai/ideogram-v2",
    "ideogram-ai/ideogram-v2-turbo",
    "recraft-ai/recraft-v3",
    "recraft-ai/recraft-v4",
    # --- VIDEO ---
    "kwaivgi/kling-v1.6-pro",
    "tencent/hunyuan-video",
    "google/veo-3.1",
    "openai/sora-2",
    "minimax/video-01",
    "luma/ray",
    "wan-ai/wan2.1-video",
    # --- AUDIO ---
    "suno-ai/bark",
    "meta/musicgen",
    "meta/musicgen-melody",
    "openai/whisper",
    "stability-ai/stable-audio-2.5",
    "minimax/speech-02",
    "elevenlabs/eleven-multilingual-v2",
    # --- TEXT / CHAT ---
    "google/gemini-2.5-flash",
    "google/gemini-3.1-pro",
    "google/gemini-3-pro",
    "openai/gpt-5-nano",
    "openai/gpt-5-mini",
    "openai/gpt-5",
    "openai/gpt-5.2",
    "openai/gpt-4.1-nano",
    "openai/gpt-4o",
    "openai/o4-mini",
    "anthropic/claude-4.5-sonnet",
    "anthropic/claude-4.5-haiku",
    "anthropic/claude-opus-4.6",
    "meta/meta-llama-3.1-405b-instruct",
    "meta/meta-llama-3.1-70b-instruct",
    "deepseek-ai/deepseek-r1",
    "deepseek-ai/deepseek-v3",
    "deepseek-ai/deepseek-v3.1",
    "xai/grok-4",
    "qwen/qwen3-235b-a22b-instruct-2507",
    "mistralai/mistral-large",
]


def ensure_staging_exists(cur):
    cur.execute("""
        SELECT EXISTS (SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'ai_models_staging');
    """)
    if not cur.fetchone()[0]:
        raise RuntimeError(
            "Tabelle ai_models_staging fehlt. Führe zuerst: python -m src.tools.init"
        )


def import_to_staging():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL fehlt in .env")
        return

    conn = psycopg2.connect(db_url, sslmode="require")
    cur = conn.cursor()
    ensure_staging_exists(cur)

    print(f"📥 Lade {len(DEFAULT_BEST_MODELS)} Best-of-Modelle von Replicate...")
    ok = 0
    fail = 0

    for full_id in DEFAULT_BEST_MODELS:
        try:
            model = replicate.models.get(full_id)
            row = model_to_row(model, full_id)
            if not row:
                print(f"   ⚠️ {full_id}: Kein Schema gefunden, übersprungen")
                fail += 1
                continue

            cur.execute("""
                INSERT INTO ai_models_staging (
                    key, replicate_id, name, description, base_cost_usd, internal_cost,
                    provider, model_type, menu_path, input_schema, output_schema, example_data,
                    is_approved, manual_override
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 0)
                ON CONFLICT (key) DO UPDATE SET
                    replicate_id = EXCLUDED.replicate_id,
                    base_cost_usd = EXCLUDED.base_cost_usd,
                    internal_cost = EXCLUDED.internal_cost,
                    model_type = EXCLUDED.model_type,
                    menu_path = EXCLUDED.menu_path,
                    input_schema = EXCLUDED.input_schema,
                    output_schema = EXCLUDED.output_schema,
                    example_data = EXCLUDED.example_data,
                    is_approved = 1,
                    last_checked = NOW();
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
            print(f"   ✅ {row['name']} ({row['menu_path']}, {row['internal_cost']} Credits)")
            ok += 1
        except Exception as e:
            conn.rollback()
            print(f"   ❌ {full_id}: {e}")
            fail += 1

    cur.close()
    conn.close()
    print(f"\n✅ Fertig: {ok} importiert, {fail} fehlgeschlagen.")


if __name__ == "__main__":
    import_to_staging()
