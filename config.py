import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from aiogram import Bot


DIR_PROJECT = Path(__file__).parent
if 'config.py' not in [p.name for p in DIR_PROJECT.iterdir()]:
    raise FileNotFoundError(f"config.py not in {DIR_PROJECT}")

DIR_GLOBAL = DIR_PROJECT.parent
if DIR_GLOBAL.name != 'Trading':
    raise FileNotFoundError(f'Project must be in `Trading` directory.')
sys.path.append(str(DIR_GLOBAL.absolute()))

TOKENS_READ_ONLY, TOKENS_FULL_ACCESS, DIR_CANDLES, DIR_CANDLES_1DAY, DIR_CANDLES_1MIN = None, None, None, None, None
from config_global import TOKENS_READ_ONLY, TOKENS_FULL_ACCESS, DIR_CANDLES, DIR_CANDLES_1DAY, DIR_CANDLES_1MIN # noqa

FILEPATH_LOGGER = (DIR_PROJECT / DIR_PROJECT.name).with_suffix('.log')
FILEPATH_ENV = DIR_PROJECT / '.env'


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=FILEPATH_ENV, env_file_encoding='utf-8')

    CHANEL_ID: str = '-1002109737146'
    BOT_TOKEN: str
    ANOMALY_VOLUME_COEFFICIENT: int = 5
    DAYS_LOOK_BACK: int = 90
    MINUTES_FROM_START: int = 15

    bot: Bot | None = None


cfg = Config()
