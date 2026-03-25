"""
gen/media_helpers.py – Medien-Konvertierung und Schema-Prüfung

Konvertiert verschiedene Medien-Spezifikationen in MediaFile-Objekte und prüft,
ob ein Modell-Schema Medien-Input (Bild, Video, Audio, Dokument) erwartet.
- path_to_mediafile: Wandelt path (str), {path, type}-Dict oder MediaFile in MediaFile um.
- ctx_media_to_list: Liest media_paths aus Context und konvertiert zu List[MediaFile].
- schema_requires_media: Prüft input_schema auf Media-Keys (image, video, audio, file, etc.).
"""

import os

from src.domain.entities import MediaFile, MediaType

EXT_BY_CONTENT = {"photo": ".jpg", "video": ".mp4", "document": None}


def path_to_mediafile(path_spec) -> MediaFile:
    """Konvertiert path (str), {path, type}-Dict oder MediaFile zu MediaFile."""
    if isinstance(path_spec, MediaFile):
        return path_spec
    if isinstance(path_spec, dict):
        return MediaFile(
            path=path_spec["path"],
            media_type=MediaType(path_spec.get("type", "image")),
        )
    ext = os.path.splitext(str(path_spec))[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".heic"]:
        mtype = MediaType.IMAGE
    elif ext in [".mp4", ".mov", ".webm", ".avi"]:
        mtype = MediaType.VIDEO
    elif ext in [".mp3", ".wav", ".m4a"]:
        mtype = MediaType.AUDIO
    else:
        mtype = MediaType.DOCUMENT
    return MediaFile(path=str(path_spec), media_type=mtype)


def ctx_media_to_list(ctx) -> list:
    """Holt media_paths aus Context und konvertiert zu List[MediaFile]."""
    raw = ctx.get("media_paths") or []
    return [path_to_mediafile(p) for p in raw]


MEDIA_KEYWORDS = [
    "image", "images", "img", "photo", "init_image", "target_image", "swap_image",
    "input_image", "control_image", "mask", "redux_image",
    "start_image", "end_image", "reference_images",
    "input_reference",
    "first_frame_image",
    "video", "videos", "input_video", "audio", "input_audio",
    "file", "document",
]

# Modelle, die NUR Image-to-Video unterstützen (kein Text-to-Video).
# Replicate-Schema markiert start_image/end_image oft als optional, die API verlangt sie aber.
IMG2VIDEO_ONLY_MODELS = ["kling-v1.6-pro", "kwaivgi/kling-v1.6-pro"]


def model_requires_image_for_video(model) -> bool:
    """
    True wenn das Modell nur Image-to-Video unterstützt (z.B. Kling v1.6 Pro).
    Diese Modelle brauchen start_image, end_image oder reference_images – ohne Bild schlägt die API fehl.
    """
    if not model:
        return False
    rid = (model.replicate_id or "").lower()
    key = (getattr(model, "key", "") or "").lower()
    for m in IMG2VIDEO_ONLY_MODELS:
        if m in rid or m in key:
            return True
    return False


def schema_requires_media(input_schema: dict, model=None) -> bool:
    """
    Prüft, ob Medien-Input (Bild/Video/Audio) PFLICHT ist.
    True wenn: (a) Media-Key in 'required' steht, oder
    (b) Modell nur Image-to-Video unterstützt (z.B. Kling v1.6 Pro).
    """
    if model_requires_image_for_video(model):
        return True
    if not input_schema or not isinstance(input_schema, dict):
        return False
    required = input_schema.get("required") or []
    for req_key in required:
        if isinstance(req_key, str):
            k = req_key.lower()
            if any(m in k for m in MEDIA_KEYWORDS):
                return True
    return False


def schema_allows_multiple_media(input_schema: dict) -> bool:
    """
    Prüft, ob das Schema mehrere Medien (z.B. images als Array) erlaubt.
    """
    if not input_schema or not isinstance(input_schema, dict):
        return False
    props = input_schema.get("properties") or {}
    for key, p in props.items():
        if not isinstance(p, dict):
            continue
        k_lower = key.lower()
        if any(m in k_lower for m in MEDIA_KEYWORDS) and p.get("type") == "array":
            return True
    return False
