import threading
import time
import telebot
from flask import Flask

# --- 1. KONFIGURATION IMPORTIEREN ---
# settings.py lädt automatisch die .env und validiert Tokens
from src.config.settings import config
from src.config.models import AI_MODELS

# --- 2. INFRASTRUKTUR (WERKZEUGE) IMPORTIEREN ---
from src.infrastructure.db.memory_repo import InMemoryUserRepo
from src.infrastructure.ai.unified_client import UnifiedAIClient # <--- NEU

# --- 3. APPLICATION (LOGIK) IMPORTIEREN ---
from src.application.services import GenerationService

# --- 4. PRESENTATION (UI) IMPORTIEREN ---
from src.presentation.telegram.bot import setup_bot

# --- WEBSERVER SETUP (FÜR RENDER HEALTHCHECKS) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    """
    Dieser Endpunkt wird von Render.com regelmäßig aufgerufen,
    um zu prüfen, ob der Bot noch lebt.
    """
    return "🤖 System Status: ONLINE", 200

def run_web_server():
    """Startet den Flask Server im Hintergrund."""
    print(f"🌍 Starte Webserver auf Port {config.PORT}...")
    # use_reloader=False ist wichtig, damit Flask nicht den Main-Thread blockiert/doppelt startet
    app.run(host='0.0.0.0', port=config.PORT, use_reloader=False)

# --- HAUPTPROGRAMM ---
def main():
    print("🚀 Initialisiere Bot System...")

    # SCHRITT A: Infrastruktur erstellen
    # Wir entscheiden uns hier konkret für die Memory-DB und Replicate.
    # Später könnte man hier 'SqlUserRepo()' nutzen, ohne den Rest des Codes zu ändern.
    user_repository = InMemoryUserRepo()
    ai_provider = UnifiedAIClient(
        replicate_key=config.REPLICATE_API_TOKEN, 
        sonauto_key=config.SONAUTO_API_KEY  # <--- Einfacher Zugriff!
    )

    # SCHRITT B: Service Layer erstellen (Dependency Injection)
    # Wir geben dem Service die Werkzeuge, die er braucht.
    generation_service = GenerationService(
        repo=user_repository, 
        ai=ai_provider
    )
    print("✅ Service Layer initialisiert.")

    # SCHRITT C: Telegram Bot vorbereiten
    try:
        bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Bots: {e}")
        return

    # SCHRITT D: Bot mit Logik verkabeln
    # Wir übergeben den Service und die Modell-Liste an das UI-System
    setup_bot(bot, generation_service, AI_MODELS)
    print("✅ Telegram Handler registriert.")

    # SCHRITT E: Webserver starten (Separater Thread)
    # Damit Render den Bot nicht killt, weil er auf Port 80/443 nicht antwortet.
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    # SCHRITT F: Bot starten (Polling Loop)
    print(f"🤖 Bot ist bereit und hört zu! (Umgebung: {config.APP_ENV})")
    
    try:
        # infinity_polling ist stabiler als polling, da es bei Netzwerkfehlern auto-restartet
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ KRITISCHER ABSTURZ: {e}")
        # In einer echten App hier Logging an Sentry o.ä. senden
        time.sleep(5)

if __name__ == "__main__":
    main()