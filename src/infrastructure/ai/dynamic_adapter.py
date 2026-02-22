import logging
import os
from typing import Any, Dict, List, Optional

class DynamicSchemaAdapter:
    def __init__(self):
        # 1. Alias-Mapping: User-Input -> Mögliche Schema-Keys
        self.field_aliases = {
            "prompt": ["prompt", "text", "caption", "input_text", "prompt_text", "story"],
            "negative_prompt": ["negative_prompt", "negative", "negative_text", "neg_prompt"],
            "width": ["width", "w"],
            "height": ["height", "h"],
            "aspect_ratio": ["aspect_ratio", "ratio", "aspect"],
            "number_of_images": ["num_outputs", "num_images", "n_images", "batch_size", "count"],
            "seed": ["seed", "random_seed"],
            "output_format": ["output_format", "format", "ext"],
            "guidance_scale": ["guidance_scale", "guidance", "scale"],
            "output_quality": ["output_quality", "quality", "jpeg_quality"]
        }
        
        # 2. Keywords für Dateityp-Erkennung in Schema-Keys
        self.type_keywords = {
            "image": ["image", "img", "photo", "face", "avatar", "mask", "init_image", "target_image", "swap_image"],
            "video": ["video", "movie", "footage", "clip", "input_video"],
            "audio": ["audio", "sound", "music", "voice", "mp3", "wav", "speech"]
        }

    # =========================================================================
    # 1. INPUT PAYLOAD BAUEN
    # =========================================================================
    def build_input_payload(self, model_schema: Dict[str, Any], user_prompt: str, file_urls: List[str] = None, **kwargs) -> Dict:
        """
        Erstellt den API-Payload.
        model_schema ist hier bereits ein DICT (kommt so aus der Entity).
        """
        # Falls das Schema leer ist ({} oder None), Fallback
        if not model_schema or not isinstance(model_schema, dict):
            return {"prompt": user_prompt}

        properties = model_schema.get("properties", {})
        payload = {}

        # A. Defaults setzen
        for key, props in properties.items():
            if "default" in props:
                payload[key] = props["default"]

        # B. Prompt setzen
        prompt_key = self._find_schema_key(properties, self.field_aliases["prompt"])
        if prompt_key and user_prompt:
            payload[prompt_key] = user_prompt

        # C. Dateien zuweisen (Smart Logic mit x-order)
        if file_urls:
            self._map_files_to_schema(payload, properties, file_urls)

        # D. Extra Parameter (kwargs) mappen
        for param, value in kwargs.items():
            if value is not None:
                schema_key = self._find_schema_key(properties, self.field_aliases.get(param, [param]))
                if schema_key:
                    payload[schema_key] = value

        return payload

    def _map_files_to_schema(self, payload: Dict, properties: Dict, file_urls: List[str]):
        """Ordnet User-Dateien den richtigen Schema-Slots zu."""
        
        # 1. Schema-Slots identifizieren
        schema_slots = []
        for key, props in properties.items():
            # Check 1: Explizites URI Format
            is_uri = props.get("format") == "uri"
            
            # Check 2: Name enthält Keywords (aber kein Integer/Boolean!)
            type_def = props.get("type", "string")
            is_string_or_undef = type_def not in ["integer", "number", "boolean"]
            name_match = any(k in key.lower() for k in ["image", "video", "audio", "file", "path", "mask"])
            
            # Ignoriere output_format
            if key in ["output_format", "format"]:
                continue

            if is_uri or (name_match and is_string_or_undef):
                # Versuche den erwarteten Typ zu erraten
                slot_type = "unknown"
                for t_name, keywords in self.type_keywords.items():
                    if any(k in key.lower() for k in keywords):
                        slot_type = t_name
                        break
                
                schema_slots.append({
                    "key": key,
                    "order": props.get("x-order", 999), # Default Order hoch setzen
                    "type": slot_type
                })

        # Nach x-order sortieren (Wichtig für Face Swap: Target=0, Swap=1)
        schema_slots.sort(key=lambda x: x["order"])

        # 2. User-Dateien klassifizieren
        user_files = []
        for url in file_urls:
            ftype = "unknown"
            ext = os.path.splitext(url.lower())[1]
            if ext in [".jpg", ".jpeg", ".png", ".webp", ".heic"]: ftype = "image"
            elif ext in [".mp4", ".mov", ".webm", ".avi", ".mkv"]: ftype = "video"
            elif ext in [".mp3", ".wav", ".m4a", ".flac", ".ogg"]: ftype = "audio"
            user_files.append({"url": url, "type": ftype})

        # 3. Zuweisung (Matching)
        used_files_indices = set()

        for slot in schema_slots:
            best_match_index = -1
            
            # Strategie A: Exakter Typ-Match
            for i, ufile in enumerate(user_files):
                if i not in used_files_indices and ufile["type"] == slot["type"]:
                    best_match_index = i
                    break
            
            # Strategie B: Fallback
            if best_match_index == -1 and (slot["type"] == "unknown" or len(user_files) == len(schema_slots)):
                 for i, ufile in enumerate(user_files):
                    if i not in used_files_indices:
                        best_match_index = i
                        break
            
            if best_match_index != -1:
                payload[slot["key"]] = user_files[best_match_index]["url"]
                used_files_indices.add(best_match_index)

    def _find_schema_key(self, properties, candidates):
        for cand in candidates:
            if cand in properties:
                return cand
        return None

    # =========================================================================
    # 2. OUTPUT PARSING
    # =========================================================================
    def parse_output(self, raw_output: Any, output_schema: Dict = None) -> Any:
        """Extrahiert das Ergebnis (URL/Text) aus der API-Antwort."""
        
        # A. Liste
        if isinstance(raw_output, list):
            if not raw_output: return None
            if isinstance(raw_output[0], str):
                return raw_output[0] 
            return raw_output[0]

        # B. Dictionary
        if isinstance(raw_output, dict):
            for k in ["output", "video", "audio", "image", "url", "file", "result"]:
                if k in raw_output:
                    return raw_output[k]
            return raw_output

        # C. String
        if isinstance(raw_output, str):
            return raw_output

        # D. Generator
        if hasattr(raw_output, '__iter__'):
            return "".join([str(x) for x in raw_output])

        return raw_output