import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import cfg, FILEPATH_LOGGER
from src.my_logging import get_logger
from src.handlers import router



async def main():
    from src.trading import get_tqbr_shares

    instruments = await get_tqbr_shares()
    print(instruments)
    exit()
    from src.trading import is_anomaly_volume

    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(token=cfg.BOT_TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == '__main__':
    get_logger(FILEPATH_LOGGER)
    try:
        asyncio.run(main())
    except Exception as ex:
        logging.error(ex, exc_info=True)
