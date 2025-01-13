from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job

from config import cfg
from src.scrapper import get_forex_cur_rates, get_funding
from src.date_utils import TZ_MOSCOW


class AlertForexCurRates:
    def append_to_scheduler(self, scheduler: AsyncIOScheduler) -> Job:
        return scheduler.add_job(
            func=self.get_forex_cur_rates_and_send_message,
            trigger='cron',
            day_of_week='mon-fri',
            hour=12,
            minute=30,
            second=0,
            max_instances=1,
            name=self.__class__.__name__
        )

    async def get_forex_cur_rates_and_send_message(self):
        dt = datetime.now(tz=TZ_MOSCOW)
        cur_rates = await get_forex_cur_rates(dt=dt)
        cr = await get_funding(date_=dt, cur_rates=cur_rates)

        msg = []
        for cur in cr:
            d = cr[cur]
            text = (f'{cur}\n'
                    f'Rate1: {round(d['rate1'], 3)} | Rate2: {round(d['rate2'], 3)} | Rate3: {round(d['rate3'], 3)}\n'
                    f'Цена предыдущего клиринга: {str(d['last_clearing_price']).replace('.', ',')}\n'
                    f'{cur}RUBF VWAP: {str(round(d['vwap'], 3)).replace('.', ',')}\n'
                    f'Funding: {str(round(d['funding'], 5)).replace('.', ',')}\n')
            msg.append(text)
        msg = '\n'.join(msg)

        text = f'{dt.date().strftime('%d.%m.%Y')}\nПриблизительные Курсы валют и фандинг рассчитанные на основе межбанка\n\n{msg}'
        print(text)
        # await cfg.bot.send_message(chat_id=cfg.CHANEL_ID, text=text)
