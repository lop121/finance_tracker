import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import (
    create_tables,
    generate_expense_pie_chart,
    register_user,
    add_expense,
    add_income,
    get_last_transaction,
    get_user_balance,
    get_report_data,
    get_category_keyboard,
)
from waiting_confirmation import DeleteTransactionState, process_confirmation
from keyboard import (
    get_back_keyboard,
    get_confirm_keyboard,
    get_main_menu_keyboard,
    get_report_keyboard,
    get_income_expense_keyboard,
    get_time_period_keyboard,
)


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


@dp.message(lambda message: message.text == "⚖️ Баланс")
async def cmd_summary(message: Message):
    user_id = message.from_user.id

    # Вызываем функцию из database.py и получаем данные о балансе
    total_income, total_expense, balance = await get_user_balance(user_id)

    # Формируем и отправляем сообщение с балансом
    balance_message = (
        f"⚖️ *Ваш текущий баланс:*\n\n"
        f"💰 *Доходы*: {total_income} руб.\n"
        f"💸 *Расходы*: {total_expense} руб.\n"
        f"🧾 *Баланс*: {balance} руб."
    )
    await message.answer(
        balance_message, parse_mode="Markdown", reply_markup=get_main_menu_keyboard()
    )


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


@dp.message(lambda message: message.text == "💸 Статистика")
async def cmd_report(message: Message):
    await message.answer(
        "Выберите период для просмотра статистики:",
        reply_markup=get_report_keyboard(),
    )


@dp.callback_query(lambda callback: callback.data.startswith("report_"))
async def process_report(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    days = 7 if callback.data == "report_week" else 30
    report_data = await get_report_data(user_id, days)

    if report_data:
        report_message = f"📊 Статистика за последние {days} дней:\n\n"
        for row in report_data:
            type_emoji = "💰" if row["type"] == "Income" else "💸"
            report_message += (
                f"{type_emoji} {row['type']}: {row['total_amount']} руб.\n"
            )
        await callback.message.edit_text(report_message)
    else:
        await callback.message.edit_text(
            "❌ Транзакции за выбранный период не найдены."
        )

    await callback.answer()  # Закрытие уведомления после нажатия


class ReportStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_period = State()


@dp.message(lambda message: message.text == "📊 Отчет")
async def cmd_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета:",
        reply_markup=get_income_expense_keyboard(),
    )


@dp.callback_query(lambda callback: callback.data in ["Income", "Expense"])
async def process_income_expense(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    type_ = callback.data

    # Save the type in FSM storage
    await state.update_data(type=type_)
    await state.set_state(ReportStates.waiting_for_category)

    # Show categories
    await callback.message.edit_text(
        "Выберите категорию:", reply_markup=await get_category_keyboard(user_id, type_)
    )
    await callback.answer()


@dp.callback_query(
    lambda callback: callback.data.startswith("Income_")
    or callback.data.startswith("Expense_")
)
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    type_, category = callback.data.split("_", 1)

    # Save the category
    await state.update_data(category=category)
    await state.set_state(ReportStates.waiting_for_period)

    # Show time period options
    await callback.message.edit_text(
        "Выберите период:", reply_markup=get_time_period_keyboard()
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data in ["week", "month"])
async def process_time_period(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    period = callback.data

    # Get the stored data
    data = await state.get_data()
    type_ = data.get("type")
    category = data.get("category")

    days = 7 if period == "week" else 30
    report_data = await get_report_data(user_id, type_, category, days)

    # Format report
    report_message = (
        f"📊 Статистика за последние {days} дней для категории {category}:\n"
    )
    if report_data:
        for row in report_data:
            type_emoji = "💰" if row["type"] == "Income" else "💸"
            report_message += (
                f"{type_emoji} {row['type']}: {row['total_amount']} руб.\n"
            )
    else:
        report_message += "❌ Транзакции не найдены за этот период."

    await callback.message.edit_text(report_message)
    await callback.answer()
    await state.clear()


@dp.message(lambda message: message.text == "📈 График")
async def cmd_chart(message: types.Message):
    user_id = message.from_user.id
    chart_file = await generate_expense_pie_chart(user_id)

    if not chart_file:
        await message.answer("Нет данных для построения графика.")
        return

    # Используем FSInputFile для отправки фото
    photo = FSInputFile(chart_file)
    await message.answer_photo(photo)

    # Удаляем временный файл после отправки
    os.remove(chart_file)


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
