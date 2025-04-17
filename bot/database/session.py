from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config

# Создаем асинхронный движок для PostgreSQL
engine = create_async_engine(
    Config.DB_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True  # Логирование SQL-запросов (можно отключить)
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)