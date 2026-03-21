"""
Begrenzt parallele Aufrufe der Replicate Prediction-API (replicate.run / client.run).

Konfiguration: REPLICATE_MAX_CONCURRENT in Settings (Umgebungsvariable gleicher Name).
Default 1 = streng nacheinander; höhere Werte erlauben z. B. 2 parallele Generierungen.
"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager

from src.config.settings import config

logger = logging.getLogger(__name__)

_n = max(1, int(config.REPLICATE_MAX_CONCURRENT))
_replicate_semaphore = threading.Semaphore(_n)

logger.info(
    "Replicate-Konkurrenz: max. %s parallele Prediction(s) (REPLICATE_MAX_CONCURRENT)",
    _n,
)


@contextmanager
def replicate_run_slot():
    """
    Hält einen „Slot“ für genau einen Replicate-Prediction-Lauf (inkl. File-Upload vor run).
    Bei Erfolg oder Fehler wird der Slot freigegeben, der nächste wartende Thread kann starten.
    """
    _replicate_semaphore.acquire()
    try:
        yield
    finally:
        _replicate_semaphore.release()
