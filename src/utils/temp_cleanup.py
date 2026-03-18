"""
temp_cleanup.py – Hilfsfunktionen zum Aufräumen des temp/-Ordners.
"""

import os
import time


def cleanup_temp_folder(max_age_seconds: int = 3600, base_dir: str = "temp") -> int:
    """
    Löscht Dateien im temp/-Ordner, die älter als max_age_seconds sind.
    Returns: Anzahl gelöschter Dateien.
    """
    if not os.path.isdir(base_dir):
        return 0

    now = time.time()
    deleted = 0
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        try:
            if not os.path.isfile(path):
                continue
            age = now - os.path.getmtime(path)
            if age > max_age_seconds:
                os.remove(path)
                deleted += 1
        except Exception:
            continue
    return deleted

