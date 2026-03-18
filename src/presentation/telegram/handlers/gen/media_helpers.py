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


def schema_requires_media(input_schema: dict) -> bool:
    """
    Prüft, ob Medien-Input (Bild/Video/Audio) PFLICHT ist.
    Nur True, wenn ein Media-Key in 'required' steht – sonst kann der User
    mit reinem Text-Prompt starten (txt2img auch bei optionalem image).
    """
    if not input_schema or not isinstance(input_schema, dict):
        return False
    required = input_schema.get("required") or []
    media_substrings = ["image", "video", "audio", "file", "img", "photo", "document", "init_image", "target_image", "swap_image", "input_image"]
    for req_key in required:
        if isinstance(req_key, str):
            k = req_key.lower()
            if any(m in k for m in media_substrings):
                return True
    return False
