"""
gen/pending.py – Zwischenspeicher für Prompt-Optimierung

Hält die vom LLM optimierten Prompts bereit, bis der User "Akzeptieren" oder "Ablehnen" wählt.
Struktur: {user_id: {original, optimized, model_key, media_files, timestamp}}.
cleanup_pending_prompts entfernt abgelaufene Einträge (älter als PROMPT_TIMEOUT Sekunden),
um Speicher zu sparen.
"""

import logging
import time

logger = logging.getLogger(__name__)

pending_prompts = {}
PROMPT_TIMEOUT = 300  # 5 Minuten


def cleanup_pending_prompts():
    """Entfernt abgelaufene Einträge aus pending_prompts."""
    now = time.time()
    expired = [uid for uid, data in pending_prompts.items()
               if now - data.get("timestamp", 0) > PROMPT_TIMEOUT]
    for uid in expired:
        pending_prompts.pop(uid, None)
        logger.info("Prompt-Entscheidung für User %s timeout", uid)
