from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from database import create_tables, register_user
import os

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Регистрация пользователя
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    await register_user(user_id, username, first_name, last_name)

    # Ответ пользователю
    await message.answer(
        "Привет! Я твой финансовый трекер. Используй команду /add_expense чтобы добавить расход."
    )


@dp.message(Command("add_expense"))
async def cmd_add_expense(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /add_expense <сумма> <описание>")
        return
    try:
        amount = float(args[1])
        description = " ".join(args[2:])
        await add_expense(message.from_user.id, amount, description)
        await message.answer(f"Расход добавлен: {amount} руб. на {description}")
    except ValueError:
        await message.answer("Неверный формат суммы. Убедитесь, что сумма - это число.")


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
