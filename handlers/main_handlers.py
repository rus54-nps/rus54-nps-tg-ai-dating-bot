from aiogram import types
from aiogram.types import ParseMode
from aiogram import Dispatcher
from keyboards import get_main_keyboard

async def start_command(message: types.Message):
    await message.answer("Привет! Добро пожаловать в Dating Bot!", reply_markup=get_main_keyboard())

def register(dp: Dispatcher):
    dp.register_message_handler(start_command, commands="start")
    dp.register_message_handler(start_command, commands="help")
