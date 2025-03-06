from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить расход"),
                KeyboardButton(text="💰 Добавить доход"),
            ],
            [KeyboardButton(text="🗑 Удалить последнюю транзакцию")],
            [KeyboardButton(text="📜 История транзакций")],
        ],
        resize_keyboard=True,
    )
    return main_menu_keyboard


def get_back_keyboard():
    back_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return back_keyboard


def get_confirm_keyboard():
    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да✅"), KeyboardButton(text="Нет❌")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return confirm_keyboard
