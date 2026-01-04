from telebot import TeleBot
# Importiere die Registrierungs-Funktionen der Handler
from src.presentation.telegram.handlers import menu_handler, gen_handler

def setup_bot(bot: TeleBot, generation_service, model_registry: dict):
    """
    Diese Funktion wird von main.py aufgerufen.
    Sie registriert alle Logik am Bot-Objekt.
    
    :param bot: Die TeleBot Instanz
    :param generation_service: Die Business-Logik (Application Layer)
    :param model_registry: Dict aller verfügbaren AIModels (Config)
    """
    
    # 1. Menü Handler registrieren
    menu_handler.register(bot, generation_service, model_registry)
    
    # 2. Generierungs Handler registrieren
    gen_handler.register(bot, generation_service, model_registry)
    
    print("✅ Telegram Handler erfolgreich registriert.")
    
    # Hier könnten noch Error-Handler oder Middlewares registriert werden