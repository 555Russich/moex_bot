from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job

from config import cfg
from src.scrapper import get_cbr_cur_rates, get_funding
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
        date_ = datetime.now(tz=TZ_MOSCOW).date()
        cur_rates = await get_cbr_cur_rates(date_=date_ + timedelta(days=1))
        cr = await get_funding(date_=date_, cur_rates=cur_rates)

        msg = []
        for cur in cr:
            if cur not in cfg.CURRENCIES:
                continue

            d = cr[cur]
            text = (f'{cur}\n'
                    f'Курс: {d['Курс']}\n'
                    f'Цена предыдущего клиринга: {d['last_clearing_price']}\n'
                    f'{cur}RUBF VWAP: {round(d['vwap'], 3)}\n'
                    f'Funding: {round(d['funding'], 5)}\n')
            msg.append(text)
        msg = '\n'.join(msg)

        text = f'{date_.strftime('%d.%m.%Y')}\nКурсы валют с сайта ЦБ и фандинг\n\n{msg}'
        await cfg.bot.send_message(chat_id=cfg.CHANEL_ID, text=text)
