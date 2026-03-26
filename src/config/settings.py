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
        self.CREDIT_PACKAGES = [
            ("S", "100 Credits", 50, 100),   
            ("M", "500 Credits", 200, 500),  
            ("L", "1500 Credits", 500, 1500)
        ]

        # Max. parallele Replicate-Predictions (replicate.run). 1 = streng nacheinander.
        self.REPLICATE_MAX_CONCURRENT = max(1, int(os.getenv("REPLICATE_MAX_CONCURRENT", "1")))
        # URL für Mini App – nur HTTPS!
        # Railway: APP_URL manuell oder RAILWAY_PUBLIC_DOMAIN; Render: RENDER_EXTERNAL_URL
        raw = os.getenv("APP_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
        if not raw and os.getenv("RAILWAY_PUBLIC_DOMAIN"):
            raw = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
        url = raw.rstrip("/")
        self.APP_URL = url if url.startswith("https://") else ""

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