"""
Zentrales Modul zum Extrahieren von Replicate-Modell-Metadaten.
Wandelt Replicate API-Daten in das Format um, das die DB + Bot erwartet.

Klassifikationslogik (wichtig für korrektes UX):
- Output-Typ entscheidet primär über menu_path (image→Bild, text→Chat, etc.)
- image_analysis: Input hat Bild, Output ist Text (z.B. Bild beschreiben)
- txt2img: Nur Prompt-Input, Output ist Bild
- img2img: Input hat Bild + Prompt, Output ist Bild
- Vision/Chat-Modelle (GPT, Claude, Gemini): Output Text → menu_path "text"
"""
import json
import re
from typing import Any, Dict, Optional, Tuple

# --- MENÜ-HIERARCHIE (passt zu strings.py menu_*)
PATH_MAP = {
    "image": ["flux", "sdxl", "image", "draw", "dall", "imagen", "remove-bg", "esrgan", "upscale", "fill", "depth", "canny", "redux"],
    "video": ["video", "animate", "motion", "kling", "wan", "hunyuan", "runway", "minimax", "veo"],
    "text": ["llama", "gpt", "mistral", "gemini", "chat", "instruct", "claude", "deepseek", "grok"],
    "audio": ["audio", "music", "tts", "whisper", "bark", "musicgen"],
    "tools": ["remove-bg", "esrgan", "upscale"],
}

MEDIA_INPUT_KEYS = [
    "image", "images", "img", "photo", "init_image", "target_image", "swap_image",
    "input_image", "control_image", "mask", "redux_image",
    "video", "videos", "input_video",
    "audio", "input_audio",
]


def slug_from_id(full_id: str) -> str:
    """Erzeugt DB-key aus owner/name (z.B. black-forest-labs-flux-1-1-pro)."""
    return re.sub(r"[^a-z0-9]+", "-", full_id.lower().replace("/", "-").replace(":", "-")).strip("-")


def _output_is_media(output_schema: Dict, model_name: str = "", model_key: str = "") -> Optional[str]:
    """
    Prüft, ob der Output ein Medien-Typ (image/video/audio) ist.
    Returns: "image", "video", "audio" oder None (Text).
    Modellname hilft, da URI allein nicht zwischen Video/Audio/Bild unterscheidet.
    """
    if not output_schema or not isinstance(output_schema, dict):
        return None
    schema_str = json.dumps(output_schema).lower()
    name_lower = ((model_name or "") + " " + (model_key or "")).lower()
    # x-cog-array-display: concatenate → Text (Streaming)
    if "concatenate" in schema_str or "x-cog-array-type" in schema_str:
        return None
    # format: uri – Modellname zur Unterscheidung
    fmt = output_schema.get("format", "")
    items = output_schema.get("items", {})
    items_fmt = items.get("format", "") if isinstance(items, dict) else ""
    if fmt == "uri" or items_fmt == "uri":
        if any(x in name_lower for x in ["video", "kling", "veo", "sora", "hunyuan", "ray", "wan"]):
            return "video"
        if any(x in name_lower for x in ["audio", "bark", "music", "whisper", "eleven"]):
            return "audio"
        return "image"
    return None


def _input_requires_media(input_schema: Dict) -> bool:
    """Prüft, ob das Input-Schema PFLICHT-Medien (Bild/Video/Audio) hat."""
    if not input_schema or not isinstance(input_schema, dict):
        return False
    required = input_schema.get("required") or []
    for req in required:
        if isinstance(req, str) and any(m in req.lower() for m in MEDIA_INPUT_KEYS):
            return True
    return False


def _input_has_media_slot(input_props: Dict) -> bool:
    """Prüft, ob das Input-Schema überhaupt Media-Slots hat (optional oder required)."""
    if not input_props:
        return False
    for key in input_props.keys():
        if key.startswith("_"):
            continue
        if any(m in key.lower() for m in MEDIA_INPUT_KEYS):
            return True
    return False


def infer_model_type(
    model_name: str,
    description: str = "",
    input_schema: Dict = None,
    output_schema: Dict = None,
    model_key: str = "",
) -> Tuple[str, str]:
    """
    Ermittelt model_type (comma-sep) und menu_path.
    Nutzt Input- UND Output-Schema für korrekte Klassifikation:
    - Output Text + Input Bild → text, image_analysis (Bild beschreiben)
    - Output Bild + Input nur Prompt → image (txt2img)
    - Output Bild + Input Bild → image, img2img
    - Vision/Chat (GPT, Claude, Gemini): Output Text → menu_path "text"
    """
    combined = (model_name + " " + (description or "") + " " + (model_key or "")).lower()
    input_schema = input_schema or {}
    input_props = input_schema.get("properties") or {}
    prop_keys = " ".join(input_props.keys()).lower()
    output_schema = output_schema or {}

    # 1. Output-Typ ermitteln
    output_media = _output_is_media(output_schema, model_name=model_name, model_key=model_key)
    out_type_str = json.dumps(output_schema).lower()
    output_is_text = (
        not output_media
        and (
            output_schema.get("type") == "array"
            or "iterator" in out_type_str
            or "concatenate" in out_type_str
        )
    ) or (output_schema.get("type") == "string" and output_schema.get("format") != "uri")

    # 2. Input: Hat Media? Ist es Pflicht?
    input_has_media = _input_has_media_slot(input_props)
    input_requires_media = _input_requires_media(input_schema)

    types = []
    menu_path = "image"

    # --- VIDEO (Modellname hat Vorrang)
    video_keywords = ["veo", "kling", "sora", "hunyuan", "minimax-video", "ray", "wan2", "wan-video", "video-01"]
    if any(x in combined for x in video_keywords) or ("video" in prop_keys and "image" not in prop_keys):
        if output_media == "video" or any(x in combined for x in video_keywords):
            types.append("video")
            menu_path = "video"

    # --- AUDIO
    if output_media == "audio" or (not types and any(x in combined for x in ["bark", "musicgen", "whisper", "eleven", "suno"])):
        types.append("audio")
        menu_path = "audio"

    # --- TEXT / CHAT (Output ist Text) – Primär für GPT, Claude, Gemini, etc.
    chat_keywords = ["llama", "gpt", "mistral", "gemini", "chat", "instruct", "claude", "deepseek", "grok", "qwen"]
    is_chat_model = any(x in combined for x in chat_keywords)
    if output_is_text or (is_chat_model and not output_media):
        types = ["text"]
        menu_path = "text"
        if input_has_media:
            types.append("image_analysis")

    # --- IMAGE (Output ist Bild oder Bild-Generator)
    if not types:
        if output_media == "image" or any(
            x in combined for x in ["flux", "sdxl", "imagen", "draw", "dall", "remove-bg", "esrgan", "fill", "depth", "canny", "redux", "ideogram", "recraft"]
        ):
            types.append("image")
            if input_requires_media or (input_has_media and any(x in prop_keys for x in ["image", "control_image", "init_image", "mask", "target_image", "swap_image"])):
                types.append("img2img")
            menu_path = "image"

    # --- TOOLS (remove-bg, esrgan, upscale)
    tools_keywords = ["remove-bg", "remove_bg", "removebg", "esrgan", "upscale", "real-esrgan"]
    if any(x in combined for x in tools_keywords) and "image" in types:
        if "upscale" not in types:
            types.append("upscale")
        menu_path = "tools"

    if not types:
        types = ["image"]
        menu_path = "image"
    model_type = ",".join(types)
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
    key = slug_from_id(full_id)
    model_type, menu_path = infer_model_type(
        model.name,
        getattr(model, "description", "") or "",
        input_schema=input_schema,
        output_schema=output_schema,
        model_key=key,
    )

    clean_name = (model.name or full_id).replace("-", " ").replace("_", " ").title()
    desc = (getattr(model, "description", "") or "")[:500]
    # Replicate liefert je nach Modell/Owner unterschiedliche Thumbnail-Keys.
    # Für Veo ist `cover_image_url` manchmal leer, darum versuchen wir mehrere Kandidaten.
    cover = (
        getattr(model, "cover_image_url", None)
        or getattr(model, "cover_url", None)
        or getattr(model, "thumbnail_url", None)
        or getattr(model, "thumbnail", None)
        or getattr(model, "image_url", None)
        or getattr(model, "preview_image_url", None)
        or ""
    )

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
