import asyncio
import logging
from datetime import datetime, timedelta, date

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pandas import DataFrame
from tvDatafeed import TvDatafeed, Interval

from src.date_utils import DateTimeFactory, TZ_MOSCOW


async def get_cb_key_rate(cbr_rate_dt: datetime):
    async with ClientSession() as session:
        while True:
            seconds_left = (cbr_rate_dt - datetime.now(tz=TZ_MOSCOW)).total_seconds()
            if seconds_left > 10:
                sleep_time = 2
            elif seconds_left > 2:
                sleep_time = 0.5
            else:
                sleep_time = 0

            new_cb_rate = await scrap_cb_key_rate(session)
            logging.info(f'СТАВКА ЦБ: {new_cb_rate}')

            if isinstance(new_cb_rate, float):
                return new_cb_rate

            await asyncio.sleep(sleep_time)


async def scrap_cb_key_rate(session: ClientSession) -> float:
    async with session.get(url='https://www.cbr.ru/') as r:
        html = await r.text()
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


async def get_cbr_cur_rates(date_: date) -> dict:
    sleep_time = 10
    today_date = datetime.now(tz=TZ_MOSCOW).date()

    async with ClientSession() as session:
        while True:
            date_cb, cur_rates = await scrap_cb_cur_rate(session=session, date_=date_)

            if (date_cb == date_) or (date_ == today_date and date_cb < date_):
                return cur_rates

            logging.info(f'Sleeping for {sleep_time} seconds. Date on cbr.ru: {date_cb.strftime("%d.%m.%Y")}')
            await asyncio.sleep(sleep_time)


async def scrap_cb_cur_rate(session: ClientSession, date_: date) -> [datetime, dict]:
    url = f'https://www.cbr.ru/currency_base/daily?UniDbQuery.Posted=True&UniDbQuery.To={date_.strftime("%d.%m.%Y")}'

    async with session.get(url) as r:
        html = await r.text()

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


async def get_forex_cur_rates(dt: datetime) -> dict:
    tv = TvDatafeed()
    dt_from = dt.replace(hour=10, tzinfo=None)
    dt_to = dt.replace(hour=15, minute=30, tzinfo=None)
    rates_info = await get_cbr_cur_rates(dt_from.date())

    for cur_code in ['USD', 'EUR', 'CNY']:
        hist = tv.get_hist(symbol=f'{cur_code}RUB', exchange='FX_IDC', interval=Interval.in_1_minute, n_bars=86400)
        df_tod = hist.loc[dt_from:dt_to]
        rate1 = _calculate_forex_cur_rate(df_tod)
        rates_info[cur_code]['rate1'] = rate1

        rate_yes = float(rates_info[cur_code]['Курс'].replace(',', '.'))
        df_yes = hist.loc[dt_from-timedelta(days=1):dt_to-timedelta(days=1)]
        v_yes, v_tod = sum(df_yes['volume']), sum(df_tod['volume'])
        rate2 = (rate_yes*v_yes + rate1*v_tod) / (v_yes+v_tod)
        rates_info[cur_code]['rate2'] = rate2
        # print(f'rate1={round(rate1, 3)} | rate2={round(rate2, 3)}')
    return rates_info


def _calculate_forex_cur_rate(df: DataFrame) -> float:
    avg = (df['close'] + df['open'] + df['high'] + df['low']) / 4
    df = df.assign(avg=avg)
    lowest_quantile = df['avg'].quantile(0.25)
    highest_quantile = df['avg'].quantile(0.75)
    lowest_range = lowest_quantile - 1.5 * (highest_quantile - lowest_quantile)
    highest_range = highest_quantile + 1.5 * (highest_quantile - lowest_quantile)
    df = df[(df['avg'] >= lowest_range) & (df['avg'] <= highest_range)]
    return sum(df['avg'] * df['volume']) / sum(df['volume'])
