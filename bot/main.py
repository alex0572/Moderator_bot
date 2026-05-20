import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from handlers.moderation import router as moderation_router
from logging_config.setup import setup_logging
from utils.database import ActionType, Database

logger = logging.getLogger("moderation_bot")


async def on_startup(dispatcher: Dispatcher, db: Database) -> None:
    await db.connect()
    logger.info("Bot started, polling updates")


async def on_shutdown(dispatcher: Dispatcher, db: Database) -> None:
    await db.close()
    logger.info("Bot stopped")


async def main() -> None:
    setup_logging()
    db = Database()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher["db"] = db

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    dispatcher.include_router(moderation_router)

    try:
        await dispatcher.start_polling(bot, db=db)
    except Exception:
        logger.exception("Fatal error during polling")
        try:
            if db.is_connected:
                await db.log_action(
                    user_id=0,
                    chat_id=None,
                    action="Fatal polling error",
                    action_type=ActionType.ERROR,
                )
        except Exception:
            pass
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
