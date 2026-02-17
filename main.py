import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.database import Database
from bot.handlers.commands import router as commands_router
from bot.handlers.callbacks import router as callbacks_router
from bot.services.kaspa_monitor import monitor_task

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    db = Database()
    await db.init()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(commands_router, callbacks_router)

    monitor = asyncio.create_task(monitor_task(bot))

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        monitor.cancel()
        try:
            await monitor
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
