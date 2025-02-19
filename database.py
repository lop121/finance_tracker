import asyncpg
import config

async def connect_db():
    return await asyncpg.connect(config.DB_URL)

async def create_tables():
    conn = await connect_db()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            amount NUMERIC NOT NULL,
            created_at TIMESTAMP DEFAULT now()
        );
    """)
    await conn.close()
