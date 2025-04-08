import asyncio
import os
from datetime import datetime, timedelta
from aiogram import Bot
from dotenv import load_dotenv
from database import get_users_without_transactions_today

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))


async def reminder_loop():
    """
    Цикл, запускающийся один раз при старте приложения и ждущий до 20:00 каждый день.
    Если пользователь за день не внёс транзакции — ему отправляется напоминание.
    """
    while True:
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        # Если текущее время уже позже 20:00 — ждать до 20:00 следующего дня
        if now >= target_time:
            target_time += timedelta(days=1)

        sleep_duration = (target_time - now).total_seconds()
        print(f"[Напоминания] Ожидание до {target_time} ({sleep_duration:.0f} сек)")
        await asyncio.sleep(sleep_duration)

        try:
            users = await get_users_without_transactions_today()
            print(f"[Напоминания] Пользователей без транзакций сегодня: {len(users)}")

            for user_id in users:
                try:
                    await bot.send_message(
                        user_id,
                        "💡 Напоминаем: вы сегодня ещё не добавили доходы или расходы.",
                    )
                except Exception as e:
                    print(f"[Ошибка отправки] user_id={user_id}: {e}")

        except Exception as e:
            print(f"[Ошибка] Напоминания не отправлены: {e}")


# async def reminder_loop():
#     """
#     Тестовый цикл напоминаний — проверяет каждые 30 секунд.
#     """
#     while True:
#         print("[Тест] Проверка напоминаний...")
#         try:
#             users = await get_users_without_transactions_today()
#             print(f"[Тест] Пользователей без транзакций: {len(users)}")

#             for user_id in users:
#                 try:
#                     await bot.send_message(
#                         user_id,
#                         "💡 [ТЕСТ] Напоминание: вы ещё не внесли доходы/расходы."
#                     )
#                 except Exception as e:
#                     print(f"[Ошибка отправки] user_id={user_id}: {e}")

#         except Exception as e:
#             print(f"[Ошибка] Напоминания не отправлены: {e}")

#         await asyncio.sleep(30)  # Повтор через 30 секунд
