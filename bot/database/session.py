from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config

# Создаем асинхронный движок с явным указанием asyncpg
engine = create_async_engine(
    Config.DB_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,
    future=True
)

# Создаем фабрику сессий с явной привязкой к движку
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Функция для получения сессии (для зависимостей)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session