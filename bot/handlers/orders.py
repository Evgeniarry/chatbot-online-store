from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, Any
from aiogram import Router, types
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from bot.database.session import AsyncSessionLocal
from bot.database.models import Order
from sqlalchemy import select
from sqlalchemy.orm import selectinload 

router = Router()

# Состояния для пагинации
class Pagination(StatesGroup):
    orders_page = State()

# Храним состояние пагинации для каждого пользователя
user_orders_state: Dict[int, Dict[str, Any]] = {}

@router.callback_query(F.data == "order_history")
async def handle_order_history(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Инициализация состояния
    user_orders_state[user_id] = {
        "page": 0,
        "orders": [],
        "message_id": None
    }
    
    await show_orders_page(callback.message, user_id)
    await callback.answer()

async def show_orders_page(message: types.Message, user_id: int):
    state = user_orders_state.get(user_id)
    if not state:
        return
    
    page = state["page"]
    items_per_page = 5  # Количество заказов на странице
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Загружаем заказы только при первом открытии
            if not state["orders"]:
                result = await session.execute(
                    select(Order)
                    .where(Order.user_id == user_id)
                    .order_by(Order.order_date.desc())
                    .options(selectinload(Order.product))
                )
                state["orders"] = result.scalars().all()
            
            orders = state["orders"]
            total_pages = (len(orders) + items_per_page - 1) // items_per_page
            
            # Получаем заказы для текущей страницы
            page_orders = orders[page*items_per_page : (page+1)*items_per_page]
            
            if not page_orders:
                text = "📭 У вас пока нет заказов"
                keyboard = None
            else:
                response = [f"📋 Ваши заказы (страница {page+1}/{total_pages}):"]
                for order in page_orders:
                    response.append(
                        f"🆔 #{order.id} {order.product.name}\n"
                        f"💰 {order.product.price} RUB\n"
                        f"📅 {order.order_date.strftime('%Y-%m-%d %H:%M')}\n"
                        f"🔹 Статус: {order.status}\n"
                    )
                text = "\n\n".join(response)
                
                # Создаем клавиатуру с пагинацией
                builder = InlineKeyboardBuilder()
                
                if page > 0:
                    builder.button(text="⬅ Назад", callback_data="orders_prev_page")
                
                if page < total_pages - 1:
                    builder.button(text="Вперед ➡", callback_data="orders_next_page")
                
                builder.button(text="🏠 В меню", callback_data="main_menu")
                builder.adjust(2)
                
                keyboard = builder.as_markup()
            
            # Отправляем или редактируем сообщение
            if state["message_id"]:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=state["message_id"],
                    text=text,
                    reply_markup=keyboard
                )
            else:
                msg = await message.answer(text, reply_markup=keyboard)
                state["message_id"] = msg.message_id

@router.callback_query(F.data == "orders_prev_page")
async def prev_page(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_orders_state:
        user_orders_state[user_id]["page"] -= 1
        await show_orders_page(callback.message, user_id)
    await callback.answer()

@router.callback_query(F.data == "orders_next_page")
async def next_page(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_orders_state:
        user_orders_state[user_id]["page"] += 1
        await show_orders_page(callback.message, user_id)
    await callback.answer()