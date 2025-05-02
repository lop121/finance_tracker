import os
import tempfile
import asyncpg
from dotenv import load_dotenv
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import matplotlib.pyplot as plt

load_dotenv()


async def create_connection():
    return await asyncpg.connect(os.getenv("DB_URL"))


async def create_tables():
    conn = await create_connection()
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            type TEXT,
            amount NUMERIC NOT NULL,
            category_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount NUMERIC NOT NULL,
            category_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS incomes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount NUMERIC NOT NULL,
            category_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await conn.close()


async def register_user(user_id: int, username: str, first_name: str, last_name: str):
    conn = await create_connection()
    await conn.execute(
        """
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO NOTHING;
    """,
        user_id,
        username,
        first_name,
        last_name,
    )
    await conn.close()


async def add_expense(user_id, amount, category_name):
    conn = await create_connection()
    user_exists = await conn.fetchval("SELECT 1 FROM users WHERE user_id = $1", user_id)
    if not user_exists:
        raise ValueError("Пользователь не существует")

    # Проверка на пустые значения
    if not amount or not category_name:
        raise ValueError("Сумма и категория не могут быть пустыми")

    # Проверка на отрицательные значения суммы
    if amount <= 0:
        raise ValueError("Сумма расхода должна быть положительной")

    # Проверка на существование категории в базе
    category_exists = await conn.fetchval(
        "SELECT 1 FROM transactions WHERE user_id = $1 AND category_name = $2 LIMIT 1",
        user_id,
        category_name,
    )
    if not category_exists:
        raise ValueError("Категория не существует для данного пользователя")
    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category_name)
            VALUES ($1, $2, $3)
            """,
            user_id,
            amount,
            category_name,
        )

        await conn.execute(
            """
            INSERT INTO transactions (user_id, type, amount, category_name)
            VALUES ($1, 'Expense', $2, $3)
            """,
            user_id,
            amount,
            category_name,
        )
    await conn.close()


async def add_income(user_id, amount, category_name):
    conn = await create_connection()
    user_exists = await conn.fetchval("SELECT 1 FROM users WHERE user_id = $1", user_id)
    if not user_exists:
        raise ValueError("Пользователь не существует")

    # Проверка на пустые значения
    if not amount or not category_name:
        raise ValueError("Сумма и категория не могут быть пустыми")

    # Проверка на отрицательные значения суммы
    if amount <= 0:
        raise ValueError("Сумма дохода должна быть положительной")

    # Проверка на существование категории в базе
    category_exists = await conn.fetchval(
        "SELECT 1 FROM transactions WHERE user_id = $1 AND category_name = $2 LIMIT 1",
        user_id,
        category_name,
    )
    if not category_exists:
        raise ValueError("Категория не существует для данного пользователя")
    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO incomes (user_id, amount, category_name)
            VALUES ($1, $2, $3)         
    """,
            user_id,
            amount,
            category_name,
        )
        await conn.execute(
            """
            INSERT INTO transactions (user_id, type, amount, category_name)
            VALUES ($1, 'Income', $2, $3)
            """,
            user_id,
            amount,
            category_name,
        )
    await conn.close()


async def delete_last_transaction(user_id: int):
    """Удаляет последнюю транзакцию пользователя."""
    conn = await create_connection()
    try:
        row = await conn.fetchrow(
            """
            DELETE FROM transactions 
            WHERE id = (
                SELECT id FROM transactions 
                WHERE user_id = $1
                ORDER BY created_at DESC 
                LIMIT 1
            )
            RETURNING id, type, amount, category_name, created_at
            """,
            user_id,
        )
        return row
    finally:
        await conn.close()


async def get_last_transaction(user_id: int, limit: int = 5):
    """Удаляет последнюю транзакцию пользователя."""
    conn = await create_connection()
    try:
        row = await conn.fetch(
            """
            SELECT id, type, amount, category_name, created_at FROM transactions 
            WHERE user_id = $1
            ORDER BY created_at DESC 
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return row
    finally:
        await conn.close()


async def get_user_balance(user_id: int):

    # SQL-запрос для расчета баланса
    conn = await create_connection()  # создаем подключение к БД
    try:
        balance_row = await conn.fetchrow(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS total_expense
            FROM transactions
            WHERE user_id = $1
            """,
            user_id,
        )
        total_income = balance_row["total_income"]
        total_expense = balance_row["total_expense"]
        balance = total_income - total_expense

        return total_income, total_expense, balance
    finally:
        await conn.close()  # Закрываем подключение к БД


async def get_report_data(user_id: int, type_: str, category: str, days: int):
    """
    Fetch report data for a given user, type, and category within the last `days` days.

    Args:
        user_id (int): User ID
        type_ (str): Type of transaction (e.g., 'income' or 'expense')
        category (str): Transaction category name
        days (int): Number of days to filter

    Returns:
        List of rows containing type, category_name, and total_amount
    """
    conn = await create_connection()

    try:
        query = """
            SELECT type, category_name, SUM(amount) AS total_amount
            FROM transactions
            WHERE user_id = $1 
            AND type = $2 
            AND category_name = $3 
            AND created_at >= NOW() - $4 * INTERVAL '1 day'
            GROUP BY type, category_name
        """
        # Execute the query with the correct parameters
        rows = await conn.fetch(query, user_id, type_, category, days)
        return rows
    finally:
        await conn.close()


async def get_category_keyboard(user_id: int, type_: str):
    # Создаем соединение с базой данных
    conn = await create_connection()
    query = "SELECT DISTINCT category_name FROM transactions WHERE user_id = $1 AND type = $2"
    categories = await conn.fetch(query, user_id, type_)
    await conn.close()

    if not categories:
        print("net c")
    # Строим клавиатуру с кнопками для каждой категории
    buttons = []
    for category in categories:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=category["category_name"],
                    callback_data=f"{type_}_{category['category_name']}",
                )
            ]
        )

    # Создаем и возвращаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def generate_pie_chart(user_id: int, txn_type: str) -> str:
    conn = await create_connection()
    try:
        query = """
            SELECT category_name, SUM(amount) AS total
            FROM transactions
            WHERE user_id = $1 AND type = $2
            GROUP BY category_name
        """
        rows = await conn.fetch(query, user_id, txn_type)
        if not rows:
            return None

        data = {row["category_name"]: float(row["total"]) for row in rows}
        labels = list(data.keys())
        sizes = list(data.values())

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")

        tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        plt.savefig(tmp_file.name, dpi=100)
        plt.close(fig)
        return tmp_file.name

    finally:
        await conn.close()


async def get_users_without_transactions_today():
    conn = await create_connection()
    query = """
        SELECT user_id FROM users
        WHERE user_id NOT IN (
            SELECT DISTINCT user_id
            FROM transactions
            WHERE DATE(created_at) = CURRENT_DATE
        );
    """
    rows = await conn.fetch(query)
    return [row["user_id"] for row in rows]


async def get_overall_report(user_id: int, days: int):
    conn = await create_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT type, SUM(amount) AS total_amount
            FROM transactions
            WHERE user_id = $1
              AND created_at >= NOW() - ($2 * INTERVAL '1 day')
            GROUP BY type
            """,
            user_id, days
        )
        return rows
    finally:
        await conn.close()
