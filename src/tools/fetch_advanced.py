import os
import replicate
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

ELITE_MODELS = [
    "black-forest-labs/flux-1.1-pro", "black-forest-labs/flux-schnell",
    "meta/meta-llama-3.1-405b-instruct", "google-deepmind/gemini-2.5-flash",
    "tencent/hunyuan-video", "lucataco/remove-bg", "nightmareai/real-esrgan"
]

HARDWARE_RATES = {
    "gpu-t4": 0.000225, "gpu-a40-large": 0.000725, "gpu-a100-80gb": 0.0014, "gpu-h100": 0.0032
}

def calculate_costs(model_version):
    avg_time = float(model_version.average_prediction_time or 5.0)
    sku = "gpu-a40-large" # Standard-Annahme
    rate = HARDWARE_RATES.get(sku, 0.000725)
    
    base_usd = avg_time * rate
    internal_credits = int(base_usd * 100 * 3.0) # 3x Marge für Profit
    return round(base_usd, 4), max(internal_credits, 2)

def analyze_metadata(model):
    latest = model.latest_version
    schema = latest.openapi_schema.get("components", {}).get("schemas", {})
    
    # Mapping für 'type' Liste in Entity
    model_types = []
    m_name = model.name.lower()
    if "flux" in m_name or "sdxl" in m_name: model_types.append("image")
    if "video" in m_name or "hunyuan" in m_name: model_types.append("video")
    if "llama" in m_name or "gemini" in m_name: model_types.append("text")
    
    # Path Logik
    m_path = "image" if "image" in model_types else ("video" if "video" in model_types else "text")

    return {
        "types": ",".join(model_types),
        "path": m_path,
        "input": schema.get("Input", {}),
        "output": schema.get("Output", {}),
        "example": {
            "prompt": schema.get("Input", {}).get("properties", {}).get("prompt", {}).get("default", ""),
            "output_image": model.cover_image_url
        }
    }

def import_to_staging():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
    cur = conn.cursor()
    cur.execute("TRUNCATE ai_models_staging")

    for model_id in ELITE_MODELS:
        try:
            m = replicate.models.get(model_id)
            meta = analyze_metadata(m)
            usd_cost, credits = calculate_costs(m.latest_version)

            cur.execute("""
                INSERT INTO ai_models_staging (
                    key, replicate_id, name, description, base_cost_usd, internal_cost, 
                    model_type, menu_path, input_schema, output_schema, example_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                m.name, model_id, m.name.replace("-", " ").title(), 
                m.description[:200] if m.description else "",
                usd_cost, credits, meta['types'], meta['path'], 
                Json(meta['input']), Json(meta['output']), Json(meta['example'])
            ))
            print(f"✅ Staged: {m.name} ({credits} Credits)")
        except Exception as e:
            print(f"❌ Error {model_id}: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import_to_staging()