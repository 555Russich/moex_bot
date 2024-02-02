from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.filters.command import CommandObject

from config import cfg
from src.alerts.anomaly_volume import AlertAnomalyVolume


COMMAND_TEST_ANOMALY_VOLUME = CommandObject(command='test_anomaly_volume')


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command=COMMAND_TEST_ANOMALY_VOLUME.command, description=AlertAnomalyVolume.__name__)],
        scope=BotCommandScopeChat(chat_id=cfg.MY_CHAT_ID)
    )
