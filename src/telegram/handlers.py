import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from my_tinkoff.schemas import Shares
from my_tinkoff.enums import Board

from src.alerts.anomaly_volume import ParamsAnomalyVolume, AlertAnomalyVolume
from src.telegram.commands import COMMAND_TEST_ANOMALY_VOLUME


router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    logging.info(f'{message.chat.id=}')
    await message.answer("Hello")


@router.message(Command(COMMAND_TEST_ANOMALY_VOLUME.command))
async def handle_test_anomaly_volume(message: Message) -> None:
    instruments = await Shares.from_board(Board.TQBR)
    params = ParamsAnomalyVolume(minutes_from_start=5)
    avr = AlertAnomalyVolume(instruments=instruments, params=params)
    for instrument in instruments:
        if instrument.ticker == 'DELI':
            await avr.get_anomaly_volume_report_and_send_alert(instrument=instrument, chat_id=message.chat.id)
