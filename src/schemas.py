from dataclasses import dataclass

from tinkoff.invest import Instrument


@dataclass
class AnomalyVolumeReport:
    ticker: str
    volume_avg: int | float
    volume_now: int
    minutes_from_start: int
    days_look_back: int

    @property
    def as_text(self) -> str:
        return (
            f'#{self.ticker}\n'
            f'За первые {self.minutes_from_start} минут объем: {self.volume_now}\n'
            f'больше в {round(self.volume_now/self.volume_avg, 1)} раза,\n'
            f'чем в среднем: {round(self.volume_avg)} за последние {self.days_look_back} дней'
        )

    def is_anomaly_volume(self, coefficient: float) -> bool:
        if self.volume_avg * coefficient <= self.volume_now:
            return True
        return False
