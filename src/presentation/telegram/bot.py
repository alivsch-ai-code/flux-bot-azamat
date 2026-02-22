from telebot import TeleBot, types
from src.presentation.telegram.handlers import menu_handler, gen_handler, payment_handler
from src.application.daily_services import DailyService 

def setup_bot(bot: TeleBot, generation_service, model_registry: dict, db):
    # model_registry wird hier nur noch aus Kompatibilität durchgereicht, 
    # aber gen_handler nutzt jetzt db.get_all_models()
    
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🚀 Start / Menu"),
            types.BotCommand("shop", "💎 Credits"),
            types.BotCommand("help", "🆘 Help")
        ])
    except: pass

    # Registriere Handler
    menu_handler.register(bot, generation_service, model_registry, db)
    payment_handler.register(bot, db)
    
    # Hier wichtig: gen_handler nutzt jetzt DB
    gen_handler.register(bot, generation_service, model_registry, db)
    
    daily = DailyService(bot, db)
    daily.start()
    
    print("✅ Telegram Handler & Services registriert.")