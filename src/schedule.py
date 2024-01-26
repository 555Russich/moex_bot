import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from my_tinkoff.date_utils import TZ_UTC
from my_tinkoff.schemas import Shares
from my_tinkoff.enums import Board

from src.date_utils import DateTimeFactory


class Scheduler:
    instance: AsyncIOScheduler = None

    @classmethod
    def new(cls):
        scheduler = AsyncIOScheduler(
            job_defaults={'misfire_grace_time': 60},
            logger=logging.getLogger(),
            timezone=TZ_UTC
        )
        cls.instance = scheduler
        return scheduler

    @classmethod
    async def setup(cls) -> None:
        from src.alerts.anomaly_volume import ParamsAnomalyVolume, AlertAnomalyVolume

        now = DateTimeFactory.now()
        dt_stocks_open = DateTimeFactory.set_time_when_stock_market_opens(now)
        instruments_tqbr = await Shares.from_board(Board.TQBR)

        all_params = (
            ParamsAnomalyVolume(minutes_from_start=5),
            ParamsAnomalyVolume(minutes_from_start=15),
            ParamsAnomalyVolume(minutes_from_start=30),
            ParamsAnomalyVolume(minutes_from_start=60),
        )
        for params in all_params:
            aav = AlertAnomalyVolume(instruments=instruments_tqbr, params=params)
            dt_run = dt_stocks_open + timedelta(minutes=params.minutes_from_start)
            aav.append_to_scheduler(scheduler=cls.instance, hour=dt_run.hour, minute=dt_run.minute)
