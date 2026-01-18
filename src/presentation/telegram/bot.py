from telebot import TeleBot, types
from src.presentation.telegram.handlers import menu_handler, gen_handler, payment_handler
# NEU
from src.application.daily_services import DailyService 

def setup_bot(bot: TeleBot, generation_service, model_registry: dict, db):
    
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🚀 Start / Menu"),
            types.BotCommand("shop", "💎 Credits"),
            types.BotCommand("help", "🆘 Help")
        ])
    except: pass

    menu_handler.register(bot, generation_service, model_registry, db)
    payment_handler.register(bot, db)
    gen_handler.register(bot, generation_service, model_registry, db)
    
    # NEU: Daily Service starten
    daily = DailyService(bot, db)
    daily.start()
    
    print("✅ Telegram Handler & Services registriert.")