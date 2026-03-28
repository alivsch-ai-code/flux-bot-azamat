"""
Begrenzt parallele Aufrufe der Replicate Prediction-API (replicate.run / client.run).

Predictions (Create / Sync): https://replicate.com/docs/topics/predictions/create-a-prediction
Rate limits (Throttling, 429): https://replicate.com/docs/topics/predictions/rate-limits

Replicate begrenzt u. a. **Prediction-Creates** (600/min laut Doku) und andere Endpunkte
stärker. Dieses Semaphor ist **kein** Ersatz für die offiziellen Limits — es reduziert nur
die **gleichzeitigen** Requests pro Prozess (sinnvoll bei einem Bot: weniger Burst-Spitzen,
weniger parallele lange `Prefer: wait`-Verbindungen). Bei 429 antwortet die API trotzdem;
Retries passieren im Telegram-`runner` (siehe `is_rate_limit`).

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
