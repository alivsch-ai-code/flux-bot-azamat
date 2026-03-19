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
                logger.warning("Umgebungsvariable '%s' fehlt (optional)", key)

        # Optionale Einstellungen mit Standardwerten
        self.PORT = int(os.getenv("PORT", 5000))
        self.APP_ENV = os.getenv("APP_ENV", "development")
        self.START_CREDITS = 2000
        # URL für Mini App – nur HTTPS! APP_URL oder RENDER_EXTERNAL_URL (Render setzt das)
        # Lokal: ngrok http 5000 → APP_URL=https://xxx.ngrok-free.app
        raw = os.getenv("APP_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
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