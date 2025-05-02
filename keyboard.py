from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def get_main_menu_keyboard():
    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить расход"),
                KeyboardButton(text="💰 Добавить доход"),
            ],
            [KeyboardButton(text="🗑 Удалить последнюю транзакцию")],
            [
                KeyboardButton(text="📜 История транзакций"),
                KeyboardButton(text="📈 График"),
            ],
            [KeyboardButton(text="💸 Статистика"), KeyboardButton(text="📊 Отчет")],
            [KeyboardButton(text="⚖️ Баланс")],
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


def get_report_keyboard():
    # Создаем массив кнопок
    buttons = [
        [
            InlineKeyboardButton(text="📆 Неделя", callback_data="report_week"),
            InlineKeyboardButton(text="🗓️ Месяц", callback_data="report_month"),
        ]
    ]

    # Передаем массив кнопок в конструктор клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_income_expense_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="💰 Доходы", callback_data="Income"),
            InlineKeyboardButton(text="💸 Расходы", callback_data="Expense"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_time_period_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="📆 Неделя", callback_data="week"),
            InlineKeyboardButton(text="🗓️ Месяц", callback_data="month"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def chart_type_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📉 Расходы", callback_data="chart_expense"),
            InlineKeyboardButton(text="📈 Доходы", callback_data="chart_income"),
        ]
    ])
    return keyboard