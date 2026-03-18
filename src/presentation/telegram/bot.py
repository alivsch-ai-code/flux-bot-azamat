import logging
from telebot import TeleBot, types

from src.application.daily_services import DailyService
from src.presentation.telegram.handlers import gen_handler, menu_handler, payment_handler

logger = logging.getLogger(__name__)


def setup_bot(bot: TeleBot, generation_service, db) -> None:
    """Registriert Handler und startet den DailyService."""
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🚀 Start / Menu"),
            types.BotCommand("shop", "💎 Credits"),
            types.BotCommand("help", "🆘 Help"),
        ])
    except Exception as e:
        logger.warning("Bot-Commands konnten nicht gesetzt werden: %s", e)

    menu_handler.register(bot, generation_service, db)
    payment_handler.register(bot, db)
    gen_handler.register(bot, generation_service, db)

    daily = DailyService(bot, db)
    daily.start()
    