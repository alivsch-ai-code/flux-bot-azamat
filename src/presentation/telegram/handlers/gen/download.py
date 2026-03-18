"""
gen/download.py – URL-Download zu Bytes

Lädt den Inhalt einer URL herunter und gibt ihn als Bytes zurück. Versucht nacheinander
requests, urllib und httpx, falls eine Bibliothek fehlt oder fehlschlägt. Wird genutzt,
um Replicate-Delivery-URLs zu fetchen, wenn Telegram 414 bei langen URLs wirft oder
wenn ein direkter Datei-Versand nötig ist.
"""

import logging
import urllib.request

logger = logging.getLogger(__name__)


def download_url_to_bytes(url: str) -> bytes | None:
    """Lädt URL herunter, gibt Bytes zurück oder None bei Fehler."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=45)
        r.raise_for_status()
        return r.content
    except Exception as e:
        logger.warning("Download (requests) failed: %s", e)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.read()
    except Exception as e:
        logger.warning("Download (urllib) failed: %s", e)
    try:
        import httpx
        r = httpx.get(url, headers=headers, timeout=45.0)
        r.raise_for_status()
        return r.content
    except Exception as e:
        logger.warning("Download (httpx) failed: %s", e)
    return None
