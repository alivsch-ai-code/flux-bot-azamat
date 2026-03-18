"""
Zentrales Modul zum Extrahieren von Replicate-Modell-Metadaten.
Wandelt Replicate API-Daten in das Format um, das die DB + Bot erwartet.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

# --- MENÜ-HIERARCHIE (passt zu strings.py menu_*)
# Flache Struktur: image, video, audio, text, tools – keine tiefen Unterordner
PATH_MAP = {
    "image": ["flux", "sdxl", "image", "draw", "dall", "imagen", "remove-bg", "esrgan", "upscale", "fill", "depth", "canny", "redux"],
    "video": ["video", "animate", "motion", "kling", "wan", "hunyuan", "runway", "minimax", "veo"],
    "text": ["llama", "gpt", "mistral", "gemini", "chat", "instruct", "claude", "deepseek", "grok"],
    "audio": ["audio", "music", "tts", "whisper", "bark", "musicgen"],
    "tools": ["remove-bg", "esrgan", "upscale"],
}


def slug_from_id(full_id: str) -> str:
    """Erzeugt DB-key aus owner/name (z.B. black-forest-labs-flux-1-1-pro)."""
    return re.sub(r"[^a-z0-9]+", "-", full_id.lower().replace("/", "-").replace(":", "-")).strip("-")


def infer_model_type(model_name: str, description: str = "", schema_props: Dict = None) -> Tuple[str, str]:
    """
    Ermittelt model_type (comma-sep) und menu_path (für Bot-Menü).
    Flache Menüstruktur: image, video, audio, text, tools (keine Unterordner).
    Video-typische Modellnamen (Veo, Kling, Sora …) werden zuerst geprüft –
    sonst würde "image" im Schema (z.B. Referenzbild) Video-Modelle falsch als Image einstufen.
    Returns: (model_type, menu_path)
    """
    combined = (model_name + " " + (description or "")).lower()
    props = schema_props or {}
    prop_keys = " ".join(props.keys()).lower()

    types = []
    # Video: Modellname-Keywords haben Vorrang (Veo, Kling, Sora = immer Video)
    video_keywords = ["veo", "kling", "sora", "hunyuan", "minimax-video", "ray", "wan2", "wan-video", "video-01"]
    if any(x in combined for x in video_keywords):
        types.append("video")
    elif any(x in combined or x in prop_keys for x in ["video", "animate", "motion"]):
        types.append("video")
    # Image
    if any(x in combined for x in ["flux", "sdxl", "imagen", "draw", "dall", "remove-bg", "esrgan", "fill", "depth", "canny", "redux", "ideogram", "recraft"]):
        types.append("image")
    elif "image" in prop_keys and "video" not in types:
        types.append("image")
    # Text
    if any(x in combined or x in prop_keys for x in ["llama", "gpt", "mistral", "gemini", "chat", "instruct", "claude", "deepseek", "grok"]):
        types.append("text")
    # Audio
    if any(x in combined or x in prop_keys for x in ["audio", "music", "tts", "whisper", "bark", "musicgen", "eleven"]):
        types.append("audio")
    if any(x in combined for x in ["upscale", "restore", "esrgan"]):
        if "image" not in types:
            types.append("image")
        types.append("upscale")
    if any(x in combined for x in ["img2img", "image_to_image"]) or "image" in prop_keys:
        if "image" in types:
            types.append("img2img")

    if not types:
        types = ["image"]
    model_type = ",".join(types)

    main = "video" if "video" in types else "image" if "image" in types else "audio" if "audio" in types else "text" if "text" in types else types[0]
    if any(x in combined for x in ["remove-bg", "esrgan", "upscale"]) and main == "image":
        menu_path = "tools"
    else:
        menu_path = main

    return model_type, menu_path


def extract_input_schema(openapi_schema: Dict) -> Dict:
    """
    Extrahiert das Input-Schema im Format für dynamic_adapter.
    Erwartet: {"properties": {...}} oder Replicate components/schemas/Input.
    """
    if not openapi_schema:
        return {}
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    inp = schemas.get("Input", {})
    if not inp:
        return {}
    # dynamic_adapter braucht mindestens "properties"
    return inp if isinstance(inp, dict) else {}


def extract_output_schema(openapi_schema: Dict) -> Dict:
    schemas = (openapi_schema or {}).get("components", {}).get("schemas", {})
    return schemas.get("Output", {}) or {}


def get_default_prompt(input_schema: Dict) -> str:
    props = input_schema.get("properties", {})
    for key in ["prompt", "text", "input_text", "prompt_text"]:
        p = props.get(key, {})
        if isinstance(p, dict) and "default" in p:
            return str(p["default"]) or ""
    return ""


def calculate_credits(model, version=None) -> Tuple[float, int]:
    avg_sec = 5.0
    if version and getattr(version, "average_prediction_time", None):
        avg_sec = float(version.average_prediction_time)
    name = (getattr(model, "name", "") or "").lower()
    usd_per_sec = 0.000725
    if any(x in name for x in ["video", "405b", "pro", "kling", "wan", "ultra"]):
        usd_per_sec = 0.0028
    elif any(x in name for x in ["schnell", "8b", "flash", "turbo", "small"]):
        usd_per_sec = 0.0002
    if "flux-1.1-pro" in name:
        base_usd = 0.05
    elif "ultra" in name:
        base_usd = 0.06
    else:
        base_usd = avg_sec * usd_per_sec
    credits = max(int(base_usd * 100 * 3.0), 2)
    return round(base_usd, 4), credits


def model_to_row(model, full_id: str) -> Optional[Dict[str, Any]]:
    """
    Konvertiert ein Replicate-Model-Objekt in eine DB-Zeile.
    Returns dict mit: key, replicate_id, name, description, base_cost_usd, internal_cost,
    provider, model_type, menu_path, input_schema, output_schema, example_data
    """
    version = getattr(model, "latest_version", None)
    if not version or not getattr(version, "openapi_schema", None):
        return None

    schema_raw = version.openapi_schema or {}
    input_schema = extract_input_schema(schema_raw)
    output_schema = extract_output_schema(schema_raw)

    base_usd, credits = calculate_credits(model, version)
    model_type, menu_path = infer_model_type(
        model.name,
        getattr(model, "description", "") or "",
        input_schema.get("properties", {}),
    )

    key = slug_from_id(full_id)
    clean_name = (model.name or full_id).replace("-", " ").replace("_", " ").title()
    desc = (getattr(model, "description", "") or "")[:500]
    cover = getattr(model, "cover_image_url", None) or ""

    return {
        "key": key,
        "replicate_id": full_id,
        "name": clean_name,
        "description": desc,
        "base_cost_usd": base_usd,
        "internal_cost": credits,
        "provider": "replicate",
        "model_type": model_type,
        "menu_path": menu_path,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "example_data": {
            "prompt": get_default_prompt(input_schema),
            "output_image": cover,
        },
    }
