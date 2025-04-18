from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from bot.database.models import Category, Product, Order
from bot.database.session import AsyncSessionLocal
from aiogram.utils.markdown import hbold
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

router = Router(name="catalog_handlers")

# Храним состояние просмотра для каждого пользователя
user_catalog_state = {}

@router.message(Command("catalog"))
async def show_categories(message: types.Message):
    """Показать список категорий с кнопкой поиска"""
    async with AsyncSessionLocal() as session:
        categories = await session.execute(select(Category))
        categories = categories.scalars().all()
        
        builder = InlineKeyboardBuilder()
        
        # Кнопки категорий
        for category in categories:
            builder.button(
                text=category.name, 
                callback_data=f"cat_{category.id}_page_0"
            )
        
        # Кнопка поиска
        builder.button(
            text="🔍 Поиск товаров", 
            callback_data="open_search"
        )
        
        # Кнопка возврата в меню
        builder.button(
            text="🔙 Назад в меню",
            callback_data="main_menu"
        )
        
        builder.adjust(2, 1, 1)  # 2 категории в ряд, затем поиск, затем назад
        
        if not categories:
            await message.answer(
                "Каталог пока пуст",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                "🏷️ Выберите категорию или найдите товар:",
                reply_markup=builder.as_markup()
            )


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: types.CallbackQuery):
    """Показать товары выбранной категории"""
    _, cat_id, _, page = callback.data.split("_")
    cat_id = int(cat_id)
    page = int(page)
    
    async with AsyncSessionLocal() as session:
        # Получаем товары категории
        products = await session.execute(
            select(Product).where(Product.category_id == cat_id)
        )
        products = products.scalars().all()
        
        if not products:
            await callback.answer("В этой категории пока нет товаров")
            return
        
        # Сохраняем товары для пагинации
        user_catalog_state[callback.from_user.id] = {
            "products": products,
            "category_id": cat_id,
            "current_page": page
        }
        
        await display_products_page(callback.message, callback.from_user.id)
        await callback.answer()

async def display_products_page(message: types.Message, user_id: int):
    """Отобразить одну страницу товаров с кнопками заказа"""
    if user_id not in user_catalog_state:
        await message.answer("Начните просмотр каталога заново (/catalog)")
        return
    
    state = user_catalog_state[user_id]
    products = state["products"]
    cat_id = state["category_id"]
    page = state["current_page"]
    items_per_page = 5
    
    # Формируем текст сообщения
    response = [f"📦 Товары (страница {page+1}):\n"]
    for product in products[page*items_per_page : (page+1)*items_per_page]:
        response.append(
            f"▪ {product.name}\n"
            f"  Цена: {product.price} руб.\n"
            f"  Артикул: {product.article}\n"
        )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки заказа для каждого товара
    for product in products[page*items_per_page : (page+1)*items_per_page]:
        builder.button(
            text=f"🛒 Заказать {product.article}", 
            callback_data=f"order_product_{product.article}"
        )
    
    # Кнопки навигации
    builder.button(text="⬅ Назад", callback_data=f"cat_{cat_id}_page_{page-1}")
    builder.button(text="Вперед ➡", callback_data=f"cat_{cat_id}_page_{page+1}")
    builder.button(text="📋 К категориям", callback_data="back_to_cats")
    
    builder.adjust(1, 2)  # 1 кнопка заказа в ряд, 2 кнопки навигации в ряд
    
    # Отправляем/обновляем сообщение
    if "message_id" in state:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=state["message_id"],
            text="\n".join(response),
            reply_markup=builder.as_markup()
        )
    else:
        msg = await message.answer(
            "\n".join(response),
            reply_markup=builder.as_markup()
        )
        state["message_id"] = msg.message_id

@router.callback_query(F.data == "back_to_cats")
async def return_to_categories(callback: types.CallbackQuery):
    """Вернуться к списку категорий"""
    await callback.message.delete()
    await show_categories(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("order_product_"))
async def order_product_from_catalog(callback: types.CallbackQuery):
    """Оформление заказа прямо из каталога"""
    try:
        article = callback.data.split("_")[2]
        user_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Находим товар по артикулу
                product = await session.scalar(
                    select(Product).where(Product.article == article)
                )
                
                if not product:
                    await callback.answer("Товар не найден")
                    return
                
                # Создаем заказ
                new_order = Order(
                    user_id=user_id,
                    product_id=product.id,
                    quantity=1,
                    status='created'
                )
                session.add(new_order)
                await session.commit()
                
                # Формируем клавиатуру
                kb = InlineKeyboardBuilder()
                kb.add(
                    InlineKeyboardButton(
                        text="🏠 В меню",
                        callback_data="main_menu"
                    )
                )
                
                await callback.message.edit_text(
                    f"✅ Заказ оформлен!\n\n"
                    f"Товар: {product.name}\n"
                    f"Артикул: {product.article}\n"
                    f"Цена: {product.price} руб.\n"
                    f"Номер заказа: {new_order.id}",
                    reply_markup=kb.as_markup()
                )
                await callback.answer()
                
    except Exception as e:
        await callback.answer("⚠️ Ошибка при оформлении заказа")
        print(f"Order error: {type(e)} - {e}")

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    """Главное меню с основными кнопками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📋 История заказов", callback_data="order_history")],
    ])
    
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "catalog")  # Обработка нажатия кнопки "Каталог"
async def handle_catalog_button(callback: types.CallbackQuery):
    await callback.message.delete()  # Удаляем предыдущее сообщение (опционально)
    await show_categories(callback.message)  # Вызываем функцию показа категорий
    await callback.answer()  # Подтверждаем обработку

# Подключаем все обработчики к роутеру
__all__ = ['router']