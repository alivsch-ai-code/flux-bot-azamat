"""
metrics.py – einfache In-Memory-Metriken für Performance-Monitoring.

Speichert pro Key:
    count, total_duration, last_duration
"""

import threading
from typing import Dict

_lock = threading.Lock()
_stats: Dict[str, Dict[str, float]] = {}


def record_timing(name: str, duration: float) -> None:
    """Registriert eine Laufzeit (Sekunden) für die gegebene Operation."""
    with _lock:
        data = _stats.setdefault(name, {"count": 0, "total": 0.0, "last": 0.0})
        data["count"] += 1
        data["total"] += duration
        data["last"] = duration


def get_stats() -> Dict[str, Dict[str, float]]:
    """Gibt eine flache Kopie der Stats zurück (für Status-Report)."""
    with _lock:
        return {k: v.copy() for k, v in _stats.items()}

