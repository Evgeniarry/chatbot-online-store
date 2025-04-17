from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from bot.database.models import Category, Product
from bot.database.session import AsyncSessionLocal

router = Router(name="catalog_handlers")

# Храним состояние просмотра для каждого пользователя
user_catalog_state = {}

@router.message(Command("catalog"))
async def show_categories(message: types.Message):
    """Показать список категорий"""
    async with AsyncSessionLocal() as session:
        categories = await session.execute(select(Category))
        categories = categories.scalars().all()
        
        if not categories:
            await message.answer("Каталог пока пуст")
            return

        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.button(
                text=category.name, 
                callback_data=f"cat_{category.id}_page_0"  # category_id и начальная страница
            )
        builder.adjust(2)  # 2 кнопки в ряд
        
        await message.answer(
            "🏷️ Выберите категорию:",
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
    """Отобразить одну страницу товаров"""
    if user_id not in user_catalog_state:
        await message.answer("Начните просмотр каталога заново (/catalog)")
        return
    
    state = user_catalog_state[user_id]
    products = state["products"]
    cat_id = state["category_id"]
    page = state["current_page"]
    items_per_page = 5
    total_pages = (len(products) + items_per_page - 1) // items_per_page
    
    # Получаем товары для текущей страницы
    start = page * items_per_page
    end = start + items_per_page
    page_products = products[start:end]
    
    # Формируем текст сообщения
    response = [f"📦 Товары (страница {page+1}/{total_pages}):\n"]
    for product in page_products:
        response.append(
            f"▪ {product.name}\n"
            f"  Цена: {product.price} руб.\n"
            f"  Артикул: <code>{product.article}</code>\n"
        )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Кнопки пагинации
    if page > 0:
        builder.button(text="⬅ Назад", callback_data=f"cat_{cat_id}_page_{page-1}")
    if end < len(products):
        builder.button(text="Вперед ➡", callback_data=f"cat_{cat_id}_page_{page+1}")
    
    # Дополнительные кнопки
    builder.button(text="🛒 Заказать", callback_data=f"order_from_cat_{cat_id}")
    builder.button(text="📋 К категориям", callback_data="back_to_cats")
    builder.adjust(2)
    
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

@router.callback_query(F.data.startswith("order_from_cat_"))
async def order_from_catalog(callback: types.CallbackQuery):
    """Оформить заказ из каталога"""
    cat_id = int(callback.data.split("_")[3])
    await callback.answer(f"Введите /order и артикул товара из категории {cat_id}")

