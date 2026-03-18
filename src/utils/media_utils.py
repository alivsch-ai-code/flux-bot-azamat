# src/utils/media_utils.py
"""Hilfsfunktionen zur Medien-Erkennung (Bild, Video, Audio) anhand von Magic Bytes."""


def detect_media_from_bytes(data: bytes) -> tuple[str, str]:
    """
    Erkennt das Medienformat anhand der Magic Bytes.
    Returns (media_type, extension), z.B. ('image', '.webp'), ('video', '.mp4'), ('audio', '.mp3').
    """
    if not data or len(data) < 4:
        return "image", ".png"
    # Video
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "video", ".mp4"
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "video", ".webm"
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"AVI ":
        return "video", ".avi"
    # Audio
    if data[:3] == b"ID3":
        return "audio", ".mp3"
    if len(data) >= 2 and data[:2] in (b"\xff\xfb", b"\xff\xfa"):
        return "audio", ".mp3"
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WAVE":
        return "audio", ".wav"
    if data[:4] == b"OggS":
        return "audio", ".ogg"
    if data[:4] == b"fLaC":
        return "audio", ".flac"
    # Image
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image", ".png"
    if data[:3] == b"\xff\xd8\xff":
        return "image", ".jpg"
    if len(data) >= 6 and data[:6] in (b"GIF87a", b"GIF89a"):
        return "image", ".gif"
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
        return "image", ".webp"
    return "image", ".png"
