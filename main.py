import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

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

    from src.alerts.forex_cur_rates import AlertForexCurRates
    # from src.alerts.cb_cur_rates import AlertCBCurRates
    # await AlertForexCurRates().get_forex_cur_rates_and_send_message()
    # await AlertCBCurRates().get_cb_cur_rates_and_send_message()

    # from src.scrapper import get_funding, get_forex_cur_rates, get_cbr_cur_rates
    # from datetime import datetime, timedelta
    # dt = datetime.now() - timedelta(days=2)
    # cur_rates = await get_forex_cur_rates(dt=dt)
    # await get_funding(date_=dt.date(), cur_rates=cur_rates)
    #
    #
    # dt = datetime.now()
    # for i in [2, 3, 4, 5, 6, 9, 10, 11, 12, 13]:
    #     dt = dt.replace(day=i)
    #     cur_rates = await get_cbr_cur_rates(date_=(dt + timedelta(days=1)).date())
    #     cur_rates_2 = await get_funding(date_=dt.date(), cur_rates=cur_rates)
    #     print(dt)
    #     for cur in ['USD', 'EUR']:
    #         print(f'{cur=} | {cur_rates_2[cur]['Курс']} | {cur_rates_2[cur]['funding']}')

    await dp.start_polling(bot)


if __name__ == '__main__':
    get_logger(FILEPATH_LOGGER)
    try:
        asyncio.run(main())
    except Exception as ex:
        logging.error(ex, exc_info=True)
