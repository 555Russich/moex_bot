from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer("Hello")

