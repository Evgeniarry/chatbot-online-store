# Создайте файл recreate_tables.py
from bot.database.session import engine
from bot.database.models import Product, Category

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

async def recreate_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы пересозданы")

if __name__ == "__main__":
    import asyncio
    asyncio.run(recreate_tables())