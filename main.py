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


async def main():
    # from tinkoff.invest import InstrumentIdType
    # from my_tinkoff.api_calls.instruments import get_instrument_by
    # from src.trading import get_volumes_for_first_n_minutes

    # instrument = await get_instrument_by(id='APTK', id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code=Board.TQBR)
    # # print(instrument)
    # avr = await get_volumes_for_first_n_minutes(instrument=instrument, days_look_back=90, minutes_from_start=5)
    # print(avr)
    # exit()

    scheduler = Scheduler.new()
    await Scheduler.setup()
    scheduler.start()

    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(token=cfg.BOT_TOKEN, parse_mode=ParseMode.HTML)
    cfg.bot = bot
    await dp.start_polling(bot)


if __name__ == '__main__':
    get_logger(FILEPATH_LOGGER)
    try:
        asyncio.run(main())
    except Exception as ex:
        logging.error(ex, exc_info=True)
