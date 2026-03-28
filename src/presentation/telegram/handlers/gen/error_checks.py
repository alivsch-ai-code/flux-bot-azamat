"""
gen/error_checks.py – Fehlertyp-Erkennung

Ermittelt die Art von Fehlern, um im Orchestrator die richtige Reaktion auszulösen:
- is_uri_too_large: Erkennt HTTP 414 (Request-URI Too Large) – dann Datei statt URL senden.
- is_rate_limit: Erkennt 429 / Throttling – dann Retry mit Wartezeit. Passt zu Replicate
  bei Limit-Überschreitung (429, „throttled“, …), siehe:
  https://replicate.com/docs/topics/predictions/rate-limits
- is_technical_error: Prüft ob Fallback auf alternatives Modell sinnvoll ist. Kein Fallback
  bei Credits, Guthaben, NSFW, Safety, Bildqualität etc. (User-/Policy-Fehler).
"""


def is_uri_too_large(err) -> bool:
    """Prüft ob 414 Request-URI Too Large vorliegt."""
    s = str(err).lower()
    return "414" in s or "request-uri too large" in s or "uri too large" in s


def is_rate_limit(error_msg: str) -> bool:
    """Prüft ob ein 429 / Throttling-Fehler vorliegt (vgl. Replicate rate-limits)."""
    if not error_msg:
        return False
    s = str(error_msg).lower()
    return "429" in s or "throttl" in s or "rate limit" in s


def is_technical_error(error_msg: str) -> bool:
    """Prüft ob Fallback-Modell sinnvoll ist. Kein Fallback bei User/Policy-Fehlern."""
    if not error_msg:
        return False
    err = str(error_msg).lower()
    if any(x in err for x in ["credits", "guthaben", "nsfw", "safety", "bildqualität", "resolution"]):
        return False
    return True
