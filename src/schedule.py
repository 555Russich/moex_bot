import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from my_tinkoff.date_utils import TZ_MOSCOW
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
            timezone=TZ_MOSCOW
        )
        cls.instance = scheduler
        return scheduler

    @classmethod
    async def setup(cls) -> None:
        from src.alerts.anomaly_volume import ParamsAnomalyVolume, AlertAnomalyVolume

        instruments = await Shares.from_board(Board.TQBR)

        # (minutes_from_start, days_look_back, coefficient)
        all_params = (
            ParamsAnomalyVolume(minutes_from_start=5, days_look_back=90, coefficient=7),
            ParamsAnomalyVolume(minutes_from_start=15, days_look_back=90, coefficient=7),
            ParamsAnomalyVolume(minutes_from_start=30, days_look_back=90, coefficient=7),
            ParamsAnomalyVolume(minutes_from_start=60, days_look_back=90, coefficient=7),
        )
        for params in all_params:
            aav = AlertAnomalyVolume(instruments=instruments, params=params)
            now = DateTimeFactory.now()
            dt = DateTimeFactory.set_time_when_stock_market_opens(now) + timedelta(minutes=params.minutes_from_start)
            aav.append_to_scheduler(
                scheduler=cls.instance,
                hour=dt.hour,
                minute=dt.minute,
            )
