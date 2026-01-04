# src/config/settings.py
import os
from dotenv import load_dotenv

# Lädt Variablen aus einer lokalen .env Datei
load_dotenv()

class Settings:
    """
    Zentraler Ort für alle Umgebungsvariablen.
    Validiert beim Start, ob alles Wichtige da ist.
    """
    
    def __init__(self):
        # 1. PFLICHTFELDER (Bot stürzt ab, wenn diese fehlen)
        self.TELEGRAM_TOKEN = self._get_required("TELEGRAM_TOKEN")
        self.REPLICATE_API_TOKEN = self._get_required("REPLICATE_API_TOKEN")
        
        # 2. NEU: SONAUTO KEY (Optional / Warnung)
        # Wir nutzen hier NICHT _get_required, damit der Bot auch ohne Musik-Key startet.
        self.SONAUTO_API_KEY = os.getenv("SONAUTO_API_KEY")
        
        if not self.SONAUTO_API_KEY:
            print("⚠️ WARNUNG: SONAUTO_API_KEY fehlt. Musik-Funktionen werden deaktiviert.")

        # 3. Optionale Einstellungen mit Standardwerten
        self.PORT = int(os.getenv("PORT", 5000))
        self.APP_ENV = os.getenv("APP_ENV", "development") # 'production' oder 'development'
        
        # Preise und Limits
        self.START_CREDITS = 2000

    def _get_required(self, key: str) -> str:
        """Holt eine Variable oder crasht, wenn sie fehlt."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"❌ CRITICAL ERROR: Umgebungsvariable '{key}' fehlt!")
        return value

# Singleton-Instanz erstellen
try:
    config = Settings()
except ValueError as e:
    print(e)
    # Wir lassen es hier crashen, damit der Bot nicht kaputt startet
    raise e