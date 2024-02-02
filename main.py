import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from my_tinkoff.schemas import Shares
from my_tinkoff.enums import Board

from config import cfg, FILEPATH_LOGGER
from src.my_logging import get_logger
from src.telegram.handlers import router
from src.schedule import Scheduler
from src.telegram.commands import set_commands


async def main():
    scheduler = Scheduler.new()
    await Scheduler.setup()
    scheduler.start()

    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(token=cfg.BOT_TOKEN, parse_mode=ParseMode.HTML)
    cfg.bot = bot
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    get_logger(FILEPATH_LOGGER)
    try:
        asyncio.run(main())
    except Exception as ex:
        logging.error(ex, exc_info=True)
