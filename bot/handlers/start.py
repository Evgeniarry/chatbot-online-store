from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):  # Исправлено на message
    """Главное меню с основными кнопками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📋 История заказов", callback_data="order_history")],
    ])
    
    await message.answer(  # Исправлено на message.answer
        "🏠 Главное меню:",
        reply_markup=keyboard
    )
