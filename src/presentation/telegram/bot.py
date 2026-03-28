import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from src.application.daily_services import DailyService
from src.config.settings import config
from src.presentation.telegram.bot_facade import TelegramBotFacade
from src.presentation.telegram.handlers import gen_handler, group_handler, menu_handler, payment_handler
from src.presentation.telegram.runtime import set_telegram_loop

logger = logging.getLogger(__name__)


async def setup_bot(
    bot: Bot, facade: TelegramBotFacade, generation_service, db
) -> tuple[DailyService, Dispatcher]:
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="🚀 Start / Menu"),
                BotCommand(command="credits", description="💎 Current Credits"),
                BotCommand(command="shop", description="💎 Buy Credits"),
                BotCommand(command="help", description="🆘 Help"),
            ]
        )
    except Exception as e:
        logger.warning("Bot-Commands konnten nicht gesetzt werden: %s", e)

    if db.get_bot_setting("menu_mode", "commands") == "webapp" and config.APP_URL:
        try:
            webapp_url = config.APP_URL.rstrip("/") + "/webapp"
            menu_btn = TelegramBotFacade.build_menu_button_webapp("🌐 Menü", webapp_url)
            await bot.set_chat_menu_button(menu_button=menu_btn)
            logger.info("Menü-Button auf Web App gesetzt: %s", webapp_url)
        except Exception as e:
            logger.warning("Menü-Button (Web App) konnte nicht gesetzt werden: %s", e)
    else:
        try:
            await bot.set_chat_menu_button(menu_button=TelegramBotFacade.build_menu_button_commands())
        except Exception as e:
            logger.debug("Menü-Button Reset: %s", e)

    daily = DailyService(facade, db, generation_service)

    dp = Dispatcher()
    group_router = Router()
    payment_router = Router()
    menu_router = Router()
    gen_router = Router()

    group_handler.register(group_router, facade, generation_service, db)
    payment_handler.register(payment_router, facade, db)
    menu_handler.register(menu_router, facade, generation_service, db, daily_service=daily)
    gen_handler.register(gen_router, facade, generation_service, db)

    dp.include_router(group_router)
    dp.include_router(payment_router)
    dp.include_router(menu_router)
    dp.include_router(gen_router)

    daily.start()
    return daily, dp


def create_bot_and_facade(loop) -> tuple[Bot, TelegramBotFacade]:
    bot = Bot(
        token=config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    facade = TelegramBotFacade(bot, loop)
    set_telegram_loop(loop)
    return bot, facade
