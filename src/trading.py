from datetime import datetime

from tinkoff.invest import Instrument, CandleInterval, InstrumentIdType

from moex_api import MOEX
from my_tinkoff_investments.api_calls.instruments import get_shares
from my_tinkoff_investments.schemas import Shares
from my_tinkoff_investments.csv_candles import CSVCandles
from my_tinkoff_investments.api_calls.instruments import get_instrument_by
from my_tinkoff_investments.enums import Board

from src.date_utils import DatetimeRange


async def is_anomaly_volume(
        instrument: Instrument,
        dt_range_data: DatetimeRange,
        dt_range_for_check: DatetimeRange,
        coefficient: float = 5,
) -> ...:
    candles = await CSVCandles.download_or_read(instrument=instrument, interval=CandleInterval.CANDLE_INTERVAL_1_MIN)


async def get_tqbr_shares() -> Shares:
    shares = await Shares.from_board(Board.TQBR)
    for s in shares:
        print(s)
    exit()

    async with MOEX() as moex:
        tickers = await moex.get_TQBR_tickers()
        for t in tickers:
            print(t)

    return Shares([
        await get_instrument_by(id=t, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER, class_code=Board.TQBR)
        for t in tickers
    ])
