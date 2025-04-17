import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import Config
from bot.handlers import routers

async def main():
    # Инициализация бота
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Подключаем роутеры
    for router in routers:
        dp.include_router(router)

    # Создание тестовых данных (если нужно)
    if os.getenv("INIT_TEST_DATA"):
        from bot.database.test_data import create_test_data
        await create_test_data()
        print("✅ Тестовые данные созданы")

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())