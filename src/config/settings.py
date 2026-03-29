# src/config/settings.py
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPTIONAL_API_KEYS = [
    "SONAUTO_API_KEY",
    "KLING_API_KEY",
    "OPENAI_API_KEY",
    "GROK_API_KEY",
    "DEEPSEEK_API_KEY",
]


class Settings:
    """
    Zentraler Ort für alle Umgebungsvariablen.
    Validiert beim Start, ob Pflichtfelder gesetzt sind.
    """

    def __init__(self) -> None:
        # Pflichtfelder (Bot startet nicht, wenn diese fehlen)
        self.TELEGRAM_TOKEN = self._get_required("TELEGRAM_TOKEN")
        self.REPLICATE_API_TOKEN = self._get_required("REPLICATE_API_TOKEN")

        # Optionale Provider-API-Keys
        for key in OPTIONAL_API_KEYS:
            setattr(self, key, os.getenv(key))
            if not getattr(self, key):
                logger.debug("Umgebungsvariable '%s' fehlt (optional)", key)

        # Optionale Einstellungen mit Standardwerten
        self.PORT = int(os.getenv("PORT", 5000))
        self.APP_ENV = os.getenv("APP_ENV", "development")

        # START UND REFERRAL REWARDS
        self.START_CREDITS = 50
        self.REFERRAL_REWARD = 50
        #GROUP CHAT MODEL
        self.GEMINI_GROUP_MODEL = "google-gemini-2-5-flash"
        # Globale Chat-Session-Zusammenfassung: nach N Nachrichten wird via Gemini komprimiert.
        self.CHAT_SUMMARIZE_AT = max(5, int(os.getenv("CHAT_SUMMARIZE_AT", "20")))
        self.GLOBAL_CHAT_SESSION_KEY = os.getenv("GLOBAL_CHAT_SESSION_KEY", "__global_chat__")
        self._MAX_WEBAPP_PROMPT_LEN = 12000
        # (label, Anzeige, Preis in Telegram Stars XTR, Credits) — kleinste Zahlung ist 1 ⭐️
        self.CREDIT_PACKAGES = [
            ("XXS", "1 Credit (Test)", 1, 1),
            ("S", "100 Credits", 50, 100),
            ("M", "500 Credits", 200, 500),
            ("L", "1500 Credits", 500, 1500),
        ]

        # Max. parallele Replicate-Predictions (replicate.run) pro Prozess — Semaphor in
        # replicate_concurrency.py. Entlastet Bursts; offizielle API-Limits siehe:
        # https://replicate.com/docs/topics/predictions/rate-limits
        self.REPLICATE_MAX_CONCURRENT = max(1, int(os.getenv("REPLICATE_MAX_CONCURRENT", "1")))
        # Replicate sync: Prefer-wait Sekunden (1–60, clamp in unified_client). Iterator-Sammeln: REPLICATE_OUTPUT_COLLECT_MAX_SEC / REPLICATE_STREAM_MAX_CHARS.
        # Webhook-Signatur (Umgebung: REPLICATE_WEBHOOK_SIGNING_SECRET, Wert z. B. whsec_… aus dem Replicate-Dashboard)
        # https://replicate.com/docs/topics/webhooks/receive-webhook
        self.REPLICATE_WEBHOOK_SIGNING_SECRET = (os.getenv("REPLICATE_WEBHOOK_SIGNING_SECRET") or "").strip()
        if not self.REPLICATE_WEBHOOK_SIGNING_SECRET:
            logger.debug(
                "REPLICATE_WEBHOOK_SIGNING_SECRET fehlt (optional) — Video/async nutzt Fallback auf HTTP/Sync"
            )
        # URL für Mini App – nur HTTPS!
        # Railway: APP_URL manuell oder RAILWAY_PUBLIC_DOMAIN; Render: RENDER_EXTERNAL_URL
        raw = os.getenv("APP_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
        if not raw and os.getenv("RAILWAY_PUBLIC_DOMAIN"):
            raw = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
        url = raw.rstrip("/")
        self.APP_URL = url if url.startswith("https://") else ""

        # Impressum / rechtliche Anzeige (optional; Platzhalter in src/legal/impressum.py)
        self.IMPRINT_LEGAL_NAME = (os.getenv("IMPRINT_LEGAL_NAME") or "").strip()
        self.IMPRINT_ADDRESS = (os.getenv("IMPRINT_ADDRESS") or "").strip().replace("\\n", "\n")
        self.IMPRINT_EMAIL = (os.getenv("IMPRINT_EMAIL") or "").strip()
        self.IMPRINT_PHONE = (os.getenv("IMPRINT_PHONE") or "").strip()
        self.IMPRINT_RESPONSIBLE = (os.getenv("IMPRINT_RESPONSIBLE") or "").strip()
        self.IMPRINT_REG = (os.getenv("IMPRINT_REG") or "").strip()
        self.IMPRINT_VAT = (os.getenv("IMPRINT_VAT") or "").strip()
        self.LEGAL_SERVICE_NAME = (os.getenv("LEGAL_SERVICE_NAME") or "AZAMAT AI").strip()

    def _get_required(self, key: str) -> str:
        """Holt eine Variable oder wirft, wenn sie fehlt."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Umgebungsvariable '{key}' fehlt!")
        return value


try:
    config = Settings()
except ValueError as e:
    logger.critical("%s", e)
    raise