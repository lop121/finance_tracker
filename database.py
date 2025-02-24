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
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount NUMERIC NOT NULL,
            description TEXT,
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


async def add_expense(user_id, amount, description):
    conn = await create_connection()
    await conn.execute(
        """
        INSERT INTO expenses (user_id, amount, description)
        VALUES ($1, $2, $3)
    """,
        user_id,
        amount,
        description,
    )
    await conn.close()
