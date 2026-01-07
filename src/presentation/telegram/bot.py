from telebot import TeleBot
# Importiere die Registrierungs-Funktionen der Handler
from src.presentation.telegram.handlers import menu_handler, gen_handler, payment_handler

def setup_bot(bot: TeleBot, generation_service, model_registry: dict, db):
    """
    Diese Funktion wird von main.py aufgerufen.
    Sie registriert alle Logik am Bot-Objekt.
    """
    
    # 1. Menü Handler (Muss zuerst kommen für Navigation)
    menu_handler.register(bot, generation_service, model_registry, db)
    
    # 2. Payment Handler (MUSS VOR gen_handler KOMMEN!)
    # Damit der Klick auf "Shop" nicht als Prompt missverstanden wird.
    payment_handler.register(bot, db)
    
    # 3. Generierungs Handler (Enthält den "Catch-All" für Prompts)
    # Dieser muss als Letztes kommen, damit er nur Texte nimmt, die keine Befehle sind.
    gen_handler.register(bot, generation_service, model_registry, db)
    
    print("✅ Telegram Handler erfolgreich registriert (Reihenfolge: Menu -> Payment -> Gen).")