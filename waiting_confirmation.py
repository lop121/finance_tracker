# waiting_confirmation.py
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from database import delete_last_transaction


class DeleteTransactionState(StatesGroup):
    waiting_for_confirmation = State()


async def process_confirmation(message: Message, state: FSMContext):
    """Обрабатывает ответ пользователя (Да/Нет) на удаление транзакции."""
    user_reply = message.text.strip().lower()
    # Если ответ "Да"
    if user_reply == "да":
        # Получаем данные последней транзакции из состояния
        data = await state.get_data()
        row = data.get("last_transaction")

        if row:
            # Вызываем функцию для удаления транзакции
            result = await delete_last_transaction(message.from_user.id)

            if result:
                await message.answer(
                    f"Транзакция удалена: {result['category_name']} на {result['amount']} руб. ({result['created_at'].strftime('%Y-%m-%d %H:%M:%S')})"
                )
            else:
                await message.answer("Ошибка: транзакция уже удалена или отсутствует.")
        else:
            await message.answer("Ошибка: не удалось получить последнюю транзакцию.")

    # Если ответ "Нет"
    elif user_reply == "нет":
        await message.answer("Вы отменили удаление последней транзакции.")

    else:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'.")

    # Очистка состояния
    await state.clear()
