import logging
from telebot import TeleBot, types

from src.application.daily_services import DailyService
from src.config.settings import config
from src.presentation.telegram.handlers import gen_handler, group_handler, menu_handler, payment_handler

logger = logging.getLogger(__name__)


"""
Telegram Bot Wiring (Update Orchestrierung).

Dieses Modul ist bewusst klein:
- `setup_bot(...)` setzt Telegram-Commands und den Chat-Menü-Button (Commands vs WebApp)
- dann registriert es die Handler-Module:
  - `group_handler` (Gruppenmodus: Gemini-Chat, Credits, Sprache)
  - `menu_handler` (Navigation, WebApp-Aktionen, Shop/Settings)
  - `payment_handler` (Telegram Stars / Invoice callbacks)
  - `gen_handler` (Generierungs-Flow: nav/start/prompt/media)

AI/Provider-Logik steckt NICHT hier, sondern in:
- `src.application.services.GenerationService`
- `src.infrastructure.ai.unified_client.UnifiedAIClient`
"""


def setup_bot(bot: TeleBot, generation_service, db) -> None:
    """Registriert Handler und startet den DailyService."""
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🚀 Start / Menu"),
            types.BotCommand("credits", "💎 Current Credits"),
            types.BotCommand("shop", "💎 Buy Credits"),
            types.BotCommand("help", "🆘 Help"),
        ])
    except Exception as e:
        logger.warning("Bot-Commands konnten nicht gesetzt werden: %s", e)

    if db.get_bot_setting("menu_mode", "commands") == "webapp" and config.APP_URL:
        try:
            webapp_url = config.APP_URL.rstrip("/") + "/webapp"
            menu_btn = types.MenuButtonWebApp("web_app", "🌐 Menü", types.WebAppInfo(webapp_url))
            bot.set_chat_menu_button(menu_button=menu_btn)
            logger.info("Menü-Button auf Web App gesetzt: %s", webapp_url)
        except Exception as e:
            logger.warning("Menü-Button (Web App) konnte nicht gesetzt werden: %s", e)
    else:
        try:
            bot.set_chat_menu_button(menu_button=types.MenuButtonCommands("commands"))
        except Exception as e:
            logger.debug("Menü-Button Reset: %s", e)

    daily = DailyService(bot, db, generation_service)

    group_handler.register(bot, generation_service, db)
    menu_handler.register(bot, generation_service, db, daily_service=daily)
    payment_handler.register(bot, db)
    gen_handler.register(bot, generation_service, db)

    daily.start()
    