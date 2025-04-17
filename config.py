import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен Telegram-бота
    DB_URL = os.getenv("DB_URL")        # postgresql://user:password@localhost/db_name