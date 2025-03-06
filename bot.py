import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import (
    create_tables,
    register_user,
    add_expense,
    add_income,
    get_last_transaction,
)
from waiting_confirmation import DeleteTransactionState, process_confirmation
from keyboard import get_back_keyboard, get_confirm_keyboard, get_main_menu_keyboard


load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


class AddTransactionState(StatesGroup):
    waiting_for_amount_and_category = State()


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
        "Привет! Я твой финансовый трекер. Выбери действие:",
        reply_markup=get_main_menu_keyboard(),
    )


@dp.message(F.text == "➕ Добавить расход")
async def start_add_expense(message: Message, state: FSMContext):
    """Переводит бота в режим ожидания суммы и категории расхода."""
    await message.answer(
        "Введите сумму и категорию расхода через пробел (например: 500 Продукты)",
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(
        transaction_type="expense"
    )  # Сохраняем тип транзакции как расход
    await state.set_state(AddTransactionState.waiting_for_amount_and_category)


@dp.message(F.text == "💰 Добавить доход")
async def start_add_income(message: Message, state: FSMContext):
    """Переводит бота в режим ожидания суммы и категории дохода."""
    await message.answer(
        "Введите сумму и категорию дохода через пробел (например: 500 Зарплата)",
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(
        transaction_type="income"
    )  # Сохраняем тип транзакции как доход
    await state.set_state(AddTransactionState.waiting_for_amount_and_category)


@dp.message(AddTransactionState.waiting_for_amount_and_category)
async def process_transaction_input(message: Message, state: FSMContext):
    """Обрабатывает введенную сумму и категорию расхода или дохода."""
    if message.text == "🔙 Назад":
        await message.answer("Отменено.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Ошибка! Введите сумму и категорию через пробел (например: 500 Продукты или 500 Зарплата)"
        )
        return

    try:
        amount = float(args[0])
        if amount <= 0:
            await message.answer("Сумма должна быть положительной. Попробуйте снова.")
            return
        category_name = " ".join(args[1:])
        if not category_name.strip():
            await message.answer("Категория не может быть пустой.")
            return
        if category_name.isdigit():
            await message.answer("Категория не может быть числом.")
            return

        transaction_type = (await state.get_data()).get("transaction_type")

        if transaction_type == "expense":
            # Добавляем расход
            await add_expense(message.from_user.id, amount, category_name)
            await message.answer(
                f"✅ Расход добавлен: {amount} руб. на {category_name}",
                reply_markup=get_main_menu_keyboard(),
            )
        elif transaction_type == "income":
            # Добавляем доход
            await add_income(message.from_user.id, amount, category_name)
            await message.answer(
                f"✅ Доход добавлен: {amount} руб. на {category_name}",
                reply_markup=get_main_menu_keyboard(),
            )

        await state.clear()
    except ValueError:
        await message.answer(
            "Ошибка! Укажите сумму числом (например: 500 Продукты или 500 Зарплата)"
        )


@dp.message(DeleteTransactionState.waiting_for_confirmation)
async def process_confirmation_handler(message: Message, state: FSMContext):
    await process_confirmation(message, state)


@dp.message(lambda message: message.text == "🗑 Удалить последнюю транзакцию")
async def cmd_delete_last_transaction(message: Message, state: FSMContext):
    """Команда для запроса на удаление последней транзакции."""
    # Получаем последнюю транзакцию
    last_transaction = (await get_last_transaction(message.from_user.id, 1))[0]

    if last_transaction:
        # Отправляем информацию о последней транзакции
        transaction_info = f"Последняя транзакция: {last_transaction['type']}, {last_transaction['category_name']} на {last_transaction['amount']} руб. ({last_transaction['created_at'].strftime('%Y-%m-%d %H:%M:%S')})\nУдалить? (Да/Нет)"
        await message.answer(transaction_info, reply_markup=get_confirm_keyboard())

        # Сохраняем данные и переходим в ожидание ответа
        await state.update_data(last_transaction=last_transaction)

        await state.set_state(DeleteTransactionState.waiting_for_confirmation)
    else:
        await message.answer("Ошибка: нет транзакций для удаления.")


@dp.message(lambda message: message.text == "📜 История транзакций")
async def cmd_get_five_last_transactions(message: Message):
    five_last = await get_last_transaction(message.from_user.id, 5)
    info = f"Последние вашие транзакции:\n\n"

    for row in five_last:
        info += f"💰 {row['type']} | {row['amount']} руб. | {row['category_name']} | {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"

    await message.answer(info, reply_markup=get_main_menu_keyboard())


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
