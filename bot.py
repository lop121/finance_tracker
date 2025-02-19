from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio
import config
import database

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def start_command(message: Message):
    if message.text == "/start":
        user_id = message.from_user.id
        name = message.from_user.full_name

        conn = await database.connect_db()
        await conn.execute(
            "INSERT INTO users (telegram_id, name) VALUES ($1, $2) ON CONFLICT (telegram_id) DO NOTHING",
            user_id, name
        )
        await conn.close()

        await message.answer(f"Привет, {name}! Я помогу тебе отслеживать финансы.")

async def main():
    await database.create_tables()  # Создаем таблицы перед запуском бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



@dp.message()
async def add_expense(message: Message):
    if message.text.startswith("/add_expense"):
        try:
            _, amount, category = message.text.split(maxsplit=2)
            amount = float(amount)
        except ValueError:
            await message.answer("Использование: /add_expense сумма категория")
            return

        conn = await database.connect_db()
        user_id = message.from_user.id

        # Проверяем, есть ли категория
        category_id = await conn.fetchval("SELECT id FROM categories WHERE name=$1 AND user_id=$2", category, user_id)
        if not category_id:
            category_id = await conn.fetchval(
                "INSERT INTO categories (name, user_id) VALUES ($1, $2) RETURNING id", category, user_id
            )

        # Добавляем транзакцию
        await conn.execute(
            "INSERT INTO transactions (user_id, category_id, amount) VALUES ($1, $2, $3)",
            user_id, category_id, amount
        )
        await conn.close()

        await message.answer(f"✅ Записано: {amount} ₽ в категорию «{category}».")

if __name__ == "__main__":
    asyncio.run(main())