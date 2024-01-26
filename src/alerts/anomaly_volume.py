from datetime import datetime, timedelta

from tinkoff.invest import Instrument, CandleInterval, InstrumentIdType
from my_tinkoff.csv_candles import CSVCandles
from my_tinkoff.schemas import Instruments
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel

from config import cfg
from src.schemas import AnomalyVolumeReport
from src.date_utils import DateTimeFactory


class ParamsAnomalyVolume(BaseModel):
    minutes_from_start: int
    days_look_back: int = 90
    coefficient: int | float = 7


class AlertAnomalyVolume:
    def __init__(
            self,
            instruments: Instruments,
            params: ParamsAnomalyVolume,
    ) -> None:
        self._instruments = instruments
        self._p = params

    def append_to_scheduler(self, scheduler: AsyncIOScheduler, hour: int, minute: int) -> Job:
        return scheduler.add_job(
            func=self._get_all_anomaly_volume_reports,
            trigger='cron',
            day_of_week='mon-fri',
            hour=hour,
            minute=minute,
            second=0,
            max_instances=1,
            name=f'{self.__class__.__name__} | {hour=} | {minute=}'
        )

    async def _get_all_anomaly_volume_reports(self):
        for instrument in self._instruments:
            await self._get_anomaly_volume_report_and_send_alert(instrument)

    async def _get_anomaly_volume_report_and_send_alert(self, instrument: Instrument) -> None:
        avr = await self._get_anomaly_volume_report(instrument)
        if avr.is_anomaly_volume(self._p.coefficient):
            await cfg.bot.send_message(chat_id=cfg.CHANEL_ID, text=avr.as_text)

    async def _get_anomaly_volume_report(self, instrument: Instrument) -> AnomalyVolumeReport:
        to = DateTimeFactory.now()
        from_ = to - timedelta(days=self._p.days_look_back)

        candles = await CSVCandles.download_or_read(
            instrument=instrument, interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
            from_=from_, to=to,
        )
        candles = candles.remove_weekend_candles()

        first_candles_in_days = []
        day_candles = []
        for c in candles:
            if day_candles and c.time.date() > day_candles[-1].time.date() or c == candles[-1]:
                first_candles_in_days.append(day_candles)
                day_candles = [c]
            elif (DateTimeFactory.set_time_when_stock_market_opens(c.time) +
                  timedelta(minutes=self._p.minutes_from_start) > c.time):
                day_candles.append(c)

        sum_of_volumes = [sum([c.volume for c in day_candles]) for day_candles in first_candles_in_days]
        volume_now = sum_of_volumes.pop(-1)
        volume_avg = sum(sum_of_volumes) / len(sum_of_volumes)

        return AnomalyVolumeReport(
            instrument=instrument,
            volume_now=volume_now,
            volume_avg=volume_avg,
            minutes_from_start=self._p.minutes_from_start,
            days_look_back=self._p.days_look_back
        )
