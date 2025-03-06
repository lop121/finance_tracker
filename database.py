import os
import asyncpg
from dotenv import load_dotenv

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
