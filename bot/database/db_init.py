from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from .models import Base
from config import Config

engine = create_engine(Config.DB_URL)

# Создаем схему, если её нет
with engine.connect() as conn:
    if not conn.dialect.has_schema(conn, "shop_bot_schema"):
        conn.execute(CreateSchema("shop_bot_schema"))
    conn.commit()

Base.metadata.create_all(engine)
print("Таблицы созданы успешно!")