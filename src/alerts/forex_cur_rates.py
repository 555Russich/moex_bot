from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job

from config import cfg
from src.scrapper import get_forex_cur_rates
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

        msg = '\n'.join([f'{cur_code} | Rate1: {round(cur_rates[cur_code]['rate1'], 3)} | Rate2: {round(cur_rates[cur_code]['rate2'], 3)} | Rate3: {round(cur_rates[cur_code]['rate3'], 3)}' for cur_code in cfg.CURRENCIES])
        text = f'Приблизительные Курсы валют рассчитанные на основе межбанка\n{msg}'
        await cfg.bot.send_message(chat_id=cfg.CHANEL_ID, text=text)
