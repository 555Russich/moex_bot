from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job

from config import cfg
from src.scrapper import get_cbr_cur_rates
from src.date_utils import TZ_MOSCOW


class AlertCBCurRates:
    def append_to_scheduler(self, scheduler: AsyncIOScheduler) -> Job:
        return scheduler.add_job(
            func=self.get_cb_cur_rates_and_send_message,
            trigger='cron',
            day_of_week='mon-fri',
            hour=13,
            minute=50,
            second=0,
            max_instances=1,
            name=self.__class__.__name__
        )

    async def get_cb_cur_rates_and_send_message(self):
        date_ = (datetime.now(tz=TZ_MOSCOW) + timedelta(days=1)).date()
        cur_rates = await get_cbr_cur_rates(date_=date_)
        cur_rates_str = '\n'.join([f'{cur_code} - {cur_rates[cur_code]['Курс']}' for cur_code in cfg.CURRENCIES])
        text = f'Курсы валют с сайта ЦБ\n{cur_rates_str}'
        await cfg.bot.send_message(chat_id=cfg.CHANEL_ID, text=text)