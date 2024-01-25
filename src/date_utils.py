from datetime import datetime
from dataclasses import dataclass

from my_tinkoff.date_utils import DateTimeFactory as BaseDatetimeFactory


class DateTimeFactory(BaseDatetimeFactory):
    OPEN_HOUR_STOCKS = 7

    @classmethod
    def set_time_when_stock_market_opens(cls, dt: datetime) -> datetime:
        return dt.replace(hour=cls.OPEN_HOUR_STOCKS, minute=0, second=0, microsecond=0)


@dataclass
class DatetimeRange:
    start: datetime
    end: datetime
