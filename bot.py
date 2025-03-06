import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
from database import (
    create_tables,
    register_user,
    add_expense,
    add_income,
    get_last_transaction,
)
from waiting_confirmation import DeleteTransactionState, process_confirmation

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
        await message.answer("Использование: /add_expense <сумма> <категория>")
        return
    try:
        amount = float(args[1])
        if amount <= 0:
            await message.answer("Сумма расхода должна быть больше нуля.")
            return
        category_name = " ".join(args[2:])
        if not category_name.strip():  # Проверка на пустую категорию
            await message.answer("Категория расхода не может быть пустой.")
            return
        if category_name.isdigit():  # Проверка, что категория не состоит из цифр
            await message.answer("Категория не может быть числом.")
            return
        await add_expense(message.from_user.id, amount, category_name)
        await message.answer(f"Расход добавлен: {amount} руб. на {category_name}")
    except ValueError:
        await message.answer("Неверный формат суммы. Убедитесь, что сумма - это число.")


@dp.message(Command("add_income"))
async def cmd_add_income(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /add_income <сумма> <категория>")
        return
    try:
        amount = float(args[1])
        if amount <= 0:
            await message.answer("Сумма дохода должна быть больше нуля.")
            return
        category_name = " ".join(args[2:])
        if not category_name.strip():  # Проверка на пустую категорию
            await message.answer("Категория дохода не может быть пустой.")
            return
        if category_name.isdigit():  # Проверка, что категория не состоит из цифр
            await message.answer("Категория не может быть числом.")
            return
        await add_income(message.from_user.id, amount, category_name)
        await message.answer(
            f"Доход добавлен: {amount} руб. Источник - {category_name}"
        )
    except ValueError:
        await message.answer("Неверный формат суммы. Убедитесь, что сумма - это число.")


@dp.message(Command("delete_last_trans"))
async def cmd_delete_last_transaction(message: Message, state: FSMContext):
    """Команда для запроса на удаление последней транзакции."""
    # Получаем последнюю транзакцию
    last_transaction = await get_last_transaction(message.from_user.id)

    if last_transaction:
        # Отправляем информацию о последней транзакции
        transaction_info = f"Последняя транзакция: {last_transaction['category_name']} на {last_transaction['amount']} руб. ({last_transaction['created_at'].strftime('%Y-%m-%d %H:%M:%S')})\nУдалить? (Да/Нет)"
        await message.answer(transaction_info)

        # Сохраняем данные и переходим в ожидание ответа
        await state.update_data(last_transaction=last_transaction)

        await state.set_state(DeleteTransactionState.waiting_for_confirmation)
    else:
        await message.answer("Ошибка: нет транзакций для удаления.")


@dp.message(DeleteTransactionState.waiting_for_confirmation)
async def process_confirmation_handler(message: Message, state: FSMContext):
    await process_confirmation(message, state)


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
