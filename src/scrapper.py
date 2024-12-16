import asyncio
import logging
import time
from datetime import datetime, timedelta, date

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pandas import DataFrame
from tvDatafeed import TvDatafeed, Interval
from tenacity import (
    retry,
    stop_after_attempt,
    before_sleep_log,
    wait_random
)
from aiomoex import ISSClient

from src.date_utils import DateTimeFactory, TZ_MOSCOW
from src.exceptions import TvDataError


logger = logging.getLogger()


class Scrapper:
    session: ClientSession

    @retry(
        stop=stop_after_attempt(100),
        wait=wait_random(0, 2),
        before_sleep=before_sleep_log(logger, log_level=logging.DEBUG)
    )
    async def request_get_text(self, *args, **kwargs):
        async with self.session.get(*args, **kwargs) as r:
            return await r.text()

    async def __aenter__(self):
        self.session = await ClientSession().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def scrap_cb_key_rate(self) -> float:
        html = self.request_get_text(url='https://www.cbr.ru/')
        soup = BeautifulSoup(html, 'lxml')
        div_content = soup.find('a', href='/hd_base/KeyRate/').parent.parent
        divs_rate = div_content.find_all('div', class_='main-indicator_line')

        for div_rate in divs_rate:
            a_date = div_rate.find('a')
            date_str = a_date.text.strip().replace('с ', '')
            rate_date = datetime.strptime(date_str, '%d.%m.%Y').replace(tzinfo=TZ_MOSCOW)
            rate_str = div_rate.find('div', class_='main-indicator_value').text.strip()
            rate_value = float(rate_str.replace('%', '').replace(',', '.'))

            if rate_date > datetime.now(tz=TZ_MOSCOW):
                return rate_value

    async def scrap_cb_cur_rate(self, date_: date) -> [datetime, dict]:
        url = (f'https://www.cbr.ru/currency_base/daily?'
               f'UniDbQuery.Posted=True&UniDbQuery.To={date_.strftime("%d.%m.%Y")}')
        html = await self.request_get_text(url=url)

        soup = BeautifulSoup(html, 'lxml')
        date_str = soup.find('button', class_='datepicker-filter_button').text
        date_cb = datetime.strptime(date_str, '%d.%m.%Y').replace(tzinfo=TZ_MOSCOW).date()

        tbody = soup.find('table', class_='data').find('tbody')
        trs = tbody.find_all('tr')
        columns = [th.text for th in trs[0].find_all('th')]

        cur_rates = {}
        for tr in trs[1:]:
            tds = tr.find_all('td')
            cur_info = {column: td.text for column, td in zip(columns, tds)}
            cur_code = cur_info.pop('Букв. код')
            cur_rates[cur_code] = cur_info

        return date_cb, cur_rates

    async def scrap_clearing_rate(self, date_: date, cur: str) -> float:
        date_str = date_.strftime('%Y-%m-%d')
        url = f'https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities/{cur}/RUB.json?from={date_str}'

        iss = ISSClient(self.session, url=url)
        data = await iss.get()
        for d in data['securities']:
            if date_str == d['tradedate'] and d['clearing'] == 'vk':
                return d['rate']


async def get_cb_key_rate(cbr_rate_dt: datetime):
    async with Scrapper() as scrapper:
        while True:
            seconds_left = (cbr_rate_dt - datetime.now(tz=TZ_MOSCOW)).total_seconds()
            if seconds_left > 10:
                sleep_time = 2
            elif seconds_left > 2:
                sleep_time = 0.5
            else:
                sleep_time = 0

            new_cb_rate = await scrapper.scrap_cb_key_rate()
            logging.info(f'СТАВКА ЦБ: {new_cb_rate}')

            if isinstance(new_cb_rate, float):
                return new_cb_rate

            await asyncio.sleep(sleep_time)


async def get_cbr_cur_rates(date_: date) -> dict:
    start_time = time.time()
    sleep_time = 10
    today_date = datetime.now(tz=TZ_MOSCOW).date()

    async with Scrapper() as scrapper:
        while True:
            seconds_from_start = time.time() - start_time
            if seconds_from_start > 30*60:
                sleep_time = 1
            elif seconds_from_start > 20*60:
                sleep_time = 2
            if seconds_from_start > 10 * 60:
                sleep_time = 5

            date_cb, cur_rates = await scrapper.scrap_cb_cur_rate(date_=date_)

            if (date_cb == date_) or (date_ == today_date and date_cb < date_):
                return cur_rates

            logging.info(f'Sleeping for {sleep_time} seconds. Date on cbr.ru: {date_cb.strftime("%d.%m.%Y")}')
            await asyncio.sleep(sleep_time)


@retry(stop=stop_after_attempt(10), before_sleep=before_sleep_log(logger, log_level=logging.DEBUG))
async def get_forex_cur_rates(dt: datetime) -> dict:
    cur_rates = {'USD': {}, 'EUR': {}}

    tv = TvDatafeed()
    dt_from = dt.replace(hour=10, tzinfo=None)
    dt_to = dt.replace(hour=15, minute=30, tzinfo=None)
    rates_info = await get_cbr_cur_rates(dt_from.date())

    for cur_code in ['USD', 'EUR']:
        hist = tv.get_hist(symbol=f'{cur_code}RUB', exchange='FX_IDC', interval=Interval.in_1_minute, n_bars=86400)
        if hist is None:
            raise TvDataError(f'Trading View Data Feed is empty for {cur_code=}')

        df_tod = hist.loc[dt_from:dt_to]
        rate1 = _calculate_forex_cur_rate(df_tod, method=1)
        cur_rates[cur_code]['rate1'] = rate1

        rate_yes = float(rates_info[cur_code]['Курс'].replace(',', '.'))
        df_yes = hist.loc[dt_from-timedelta(days=1):dt_to-timedelta(days=1)]
        v_yes, v_tod = sum(df_yes['volume']), sum(df_tod['volume'])
        rate2 = (rate_yes*v_yes + rate1*v_tod) / (v_yes+v_tod)
        cur_rates[cur_code]['rate2'] = rate2

        rate3 = _calculate_forex_cur_rate(df_tod, method=3)
        cur_rates[cur_code]['rate3'] = rate3

        print(f'rate1={round(rate1, 3)} | rate2={round(rate2, 3)} | rate3={rate3} {type(rate3)}')
    return cur_rates


def _calculate_forex_cur_rate(df: DataFrame, method: int) -> float:
    avg = (df['close'] + df['high'] + df['low']) / 3
    df = df.assign(avg=avg)
    lowest_quantile = df['avg'].quantile(0.25)
    highest_quantile = df['avg'].quantile(0.75)

    if method == 1:
        lowest_range = lowest_quantile - 1.5 * (highest_quantile - lowest_quantile)
        highest_range = highest_quantile + 1.5 * (highest_quantile - lowest_quantile)
    elif method == 3:
        lowest_range = lowest_quantile
        highest_range = highest_quantile
    else:
        raise Exception('Method must be either 1 or 3')

    df = df[(df['avg'] >= lowest_range) & (df['avg'] <= highest_range)]
    return sum(df['avg'] * df['volume']) / sum(df['volume'])


async def get_funding(date_: date, cur_rates: dict):
    cur_params = {
        'USD': {'K1': 0.001, 'K2': 0.001, 'last_clearing_price': None, 'vwap': None},
        'EUR': {'K1': 0.001, 'K2': 0.001, 'last_clearing_price': None, 'vwap': None},
    }
    dt_from = datetime(year=date_.year, month=date_.month, day=date_.day, hour=10, tzinfo=None)
    dt_to = datetime(year=date_.year, month=date_.month, day=date_.day, hour=15, minute=30, tzinfo=None)

    tv = TvDatafeed()
    async with Scrapper() as scrapper:
        for cur, d in cur_params.items():
            # print(cur_rates[cur])
            if cur_rates[cur].get('Курс'):
                spot_rate = float(cur_rates[cur]['Курс'].replace(',', '.'))
            else:
                spot_rate = cur_rates[cur]['rate1']

            last_clearing_price = await scrapper.scrap_clearing_rate(date_=date_, cur=cur)
            cur_params[cur]['last_clearing_price'] = last_clearing_price
            cur_rates[cur]['last_clearing_price'] = last_clearing_price

            df = tv.get_hist(symbol=f'{cur}RUB.P', exchange='RUS', interval=Interval.in_1_minute, n_bars=86400)
            df = df.loc[dt_from:dt_to]
            df['cum_vol'] = df['volume'].cumsum()
            df['cum_vol_price'] = (df['volume'] * (df['high'] + df['low'] + df['close'])/3).cumsum()
            df['vwap'] = df['cum_vol_price'] / df['cum_vol']
            vwap = float(df['vwap'].iloc[-1])
            cur_rates[cur]['vwap'] = vwap

            l1 = last_clearing_price * cur_params[cur]['K1']
            l2 = last_clearing_price * cur_params[cur]['K2']
            d = vwap - spot_rate
            funding = min(l2, max(-l2, min(-l1, d) + max(l1, d)))
            cur_rates[cur]['funding'] = funding
            # print(f'{spot_rate=} | {vwap=} | {d=} | {funding=}')
    return cur_rates

    print(cur_params)
    # tv = TvDatafeed()

