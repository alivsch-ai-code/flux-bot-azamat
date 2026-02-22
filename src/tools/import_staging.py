import os
import replicate
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURATION ---

# 1. DEINE PRIORITÄTEN (Werden bevorzugt behandelt & gesucht)
PRIORITY_MODELS = [
    "black-forest-labs/flux-1.1-pro",
    "black-forest-labs/flux-schnell",
    "tencent/hunyuan-video",
    "kwaivgi/kling-v1.6-pro", 
    "wan-video/wan-2.1-1.3b",
    "meta/meta-llama-3.1-405b-instruct",
    "google/gemini-2.5-flash"
]

# 2. ZIEL-COLLECTIONS (Ganze Sammlungen laden)
TARGET_COLLECTIONS = ["official", "image-generation", "video-generation"]

# 3. ZIEL-PROVIDER & KEYWORDS (Für die breite Suche)
TARGET_PROVIDERS = ["google", "kwaivgi", "wan-video", "tencent", "black-forest-labs", "meta", "mistralai", "openai", "wavespeedai"]
TARGET_KEYWORDS = ["gemini", "kling", "wan", "flux", "llama", "video", "chat", "upscale"]


# --- HELPER FUNKTIONEN ---

def calculate_credits_safe(model, version=None):
    """
    Berechnet Credits robust. Fängt Fälle ab, wo Modelle keine Zeit-Metriken haben.
    """
    # Standard: 5 Sekunden
    avg_sec = 5.0
    
    # Versuche echte Daten zu bekommen
    if version and hasattr(version, 'average_prediction_time') and version.average_prediction_time:
        avg_sec = float(version.average_prediction_time)
    elif hasattr(model, 'metrics') and model.metrics and 'average_prediction_time' in model.metrics:
        avg_sec = float(model.metrics['average_prediction_time'])
    
    # Preis-Kategorien (USD pro Sekunde Schätzung)
    usd_per_sec = 0.000725 # Standard A40
    name = model.name.lower()
    
    if any(x in name for x in ["video", "405b", "pro", "kling", "wan", "ultra"]): 
        usd_per_sec = 0.0028 # High-End (A100/H100)
    elif any(x in name for x in ["schnell", "8b", "flash", "turbo", "small"]): 
        usd_per_sec = 0.0002 # Low-End (T4/L4)

    # Pauschalpreise für offizielle Modelle simulieren (die per Image abrechnen)
    if "flux-1.1-pro" in name: base_usd = 0.05
    elif "ultra" in name: base_usd = 0.06
    else: base_usd = avg_sec * usd_per_sec

    # 3x Marge für Profit
    final_credits = max(int(base_usd * 100 * 3.0), 2)
    return round(base_usd, 4), final_credits

def get_model_metadata(model):
    """Extrahiert Schema, Pfad und Typen intelligent."""
    version = getattr(model, 'latest_version', None)
    
    # Schema holen (Fallback auf leeres Dict)
    schema_in = {}
    schema_out = {}
    if version and hasattr(version, 'openapi_schema'):
        schema_in = version.openapi_schema.get("components", {}).get("schemas", {}).get("Input", {})
        schema_out = version.openapi_schema.get("components", {}).get("schemas", {}).get("Output", {})
    
    # Kategorie bestimmen (für Menü & Filter)
    m_name = model.name.lower()
    desc = (model.description or "").lower()
    
    types = []
    if any(x in m_name for x in ["flux", "sdxl", "image", "draw"]): types.append("image")
    if any(x in m_name or x in desc for x in ["video", "animate", "motion", "kling", "wan"]): types.append("video")
    if any(x in m_name or x in desc for x in ["llama", "chat", "gpt", "mistral", "gemini"]): types.append("text")
    if any(x in m_name for x in ["upscale", "restore", "audio", "music"]): types.append("tools")
    
    # Fallback
    if not types: types.append("image")
    main_path = types[0]
    
    return {
        "input": schema_in,
        "output": schema_out,
        "types": ",".join(types),
        "path": main_path,
        "img": model.cover_image_url
    }

# --- MAIN IMPORT LOOP ---

def run_import():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL fehlt!")
        return

    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()

    # WICHTIG: KEIN TRUNCATE MEHR!
    # Wir wollen bestehende manuelle Edits behalten.
    print("📥 Starte Smart-Import (behalte manuelle Änderungen)...")

    models_to_process = {}

    # 1. COLLECTIONS LADEN
    print(f"📚 Lade Collections: {', '.join(TARGET_COLLECTIONS)}...")
    for slug in TARGET_COLLECTIONS:
        try:
            collection = replicate.collections.get(slug)
            if collection:
                for m in collection.models:
                    models_to_process[f"{m.owner}/{m.name}"] = m
        except Exception:
            pass # Manche Collections sind evtl. leer oder privat

    # 2. SUCHE NACH PROVIDERN & KEYWORDS
    print(f"🔍 Scanne Provider & Keywords...")
    for query in TARGET_PROVIDERS + TARGET_KEYWORDS:
        try:
            results = replicate.models.search(query)
            for m in results:
                # Nur relevante Provider speichern
                if m.owner in TARGET_PROVIDERS or any(k in m.name.lower() for k in TARGET_KEYWORDS):
                    models_to_process[f"{m.owner}/{m.name}"] = m
        except Exception:
            continue

    # 3. PRIORITY MODELLE ERZWINGEN
    print("💎 Prüfe Priority-Liste...")
    for model_id in PRIORITY_MODELS:
        if model_id not in models_to_process:
            try:
                m = replicate.models.get(model_id)
                models_to_process[model_id] = m
            except:
                print(f"   ❌ Priority Modell {model_id} nicht gefunden.")

    print(f"📦 Verarbeite {len(models_to_process)} Modelle...")
    
    count = 0
    updated = 0
    skipped = 0

    for full_id, model in models_to_process.items():
        try:
            version = getattr(model, 'latest_version', None)
            base_usd, credits = calculate_credits_safe(model, version)
            meta = get_model_metadata(model)
            
            # Default Prompt suchen
            def_prompt = ""
            props = meta['input'].get("properties", {})
            if "prompt" in props and "default" in props["prompt"]:
                def_prompt = props["prompt"]["default"]

            example_data = {
                "prompt": def_prompt,
                "output_image": meta['img'],
                "path": meta['path']
            }

            clean_name = model.name.replace("-", " ").replace("_", " ").title()

            # DAS SMARTE SQL QUERY
            # Es updated nur, wenn manual_override = 0 ist!
            cur.execute("""
                INSERT INTO ai_models_staging 
                (key, replicate_id, name, description, base_cost_usd, internal_cost, 
                 model_type, menu_path, input_schema, output_schema, example_data, 
                 is_approved, manual_override)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0)
                ON CONFLICT (key) DO UPDATE SET
                    replicate_id = EXCLUDED.replicate_id,
                    base_cost_usd = EXCLUDED.base_cost_usd,
                    input_schema = EXCLUDED.input_schema,
                    output_schema = EXCLUDED.output_schema,
                    example_data = EXCLUDED.example_data,
                    last_checked = NOW(),
                    
                    -- GESCHÜTZTE FELDER (Nur Update wenn Override AUS)
                    name = CASE 
                        WHEN ai_models_staging.manual_override = 1 THEN ai_models_staging.name 
                        ELSE EXCLUDED.name 
                    END,
                    description = CASE 
                        WHEN ai_models_staging.manual_override = 1 THEN ai_models_staging.description 
                        ELSE EXCLUDED.description 
                    END,
                    internal_cost = CASE 
                        WHEN ai_models_staging.manual_override = 1 THEN ai_models_staging.internal_cost 
                        ELSE EXCLUDED.internal_cost 
                    END,
                    model_type = CASE 
                        WHEN ai_models_staging.manual_override = 1 THEN ai_models_staging.model_type 
                        ELSE EXCLUDED.model_type 
                    END,
                    menu_path = CASE 
                        WHEN ai_models_staging.manual_override = 1 THEN ai_models_staging.menu_path 
                        ELSE EXCLUDED.menu_path 
                    END;
            """, (
                model.name, full_id, clean_name,
                model.description[:500] if model.description else "",
                base_usd, credits, meta['types'], meta['path'],
                Json(meta['input']), Json(meta['output']), Json(example_data)
            ))
            
            count += 1
            if count % 20 == 0: print(f"   ... {count} verarbeitet")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {full_id}: {e}")
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Fertig! {count} Modelle im Staging aktualisiert (Skipped: {skipped}).")
    print("👉 Deine manuellen Edits (manual_override=1) wurden beibehalten.")

if __name__ == "__main__":
    run_import()