from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from bot.database.models import Product, Category
from bot.database.session import AsyncSessionLocal

router = Router(name="search_handlers")

async def perform_search(query: str, session) -> list[Product]:
    """Выполняет поиск товаров по запросу"""
    stmt = (
        select(Product)
        .join(Category)
        .options(selectinload(Product.category))
        .where(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.article.ilike(f"%{query}%"),
                Category.name.ilike(f"%{query}%")
            )
        )
        .limit(10)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def build_search_response(products: list[Product]) -> tuple[str, InlineKeyboardBuilder]:
    """Формирует ответ с результатами поиска"""
    if not products:
        return "🔍 Товары не найдены", None

    response = ["🔍 Результаты поиска:"]
    for product in products:
        response.append(
            f"{hbold(product.name)} - {product.price} руб.\n"
            f"Артикул: <code>{product.article}</code>\n"
            f"Категория: {product.category.name}\n"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в каталог", callback_data="catalog")
    builder.button(text="🏠 В меню", callback_data="main_menu")
    builder.adjust(1)

    return "\n\n".join(response), builder

@router.callback_query(F.data == "open_search")
async def open_search_handler(callback: types.CallbackQuery):
    """Активирует режим поиска из каталога"""
    await callback.message.edit_text(
        "🔍 Введите поисковый запрос:\n"
        "Пример: <code>тарелка</code>\n"
        "Или: <code>STK-001</code>\n\n"
        "Просто напишите что ищете в этом чате",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("search"))
async def search_command_handler(message: types.Message):
    """Обрабатывает команду /search"""
    try:
        query = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        await message.answer(
            "🔍 Введите поисковый запрос:\n"
            "Пример: <code>/search тарелка</code>\n"
            "Или: <code>/search STK-001</code>",
            parse_mode="HTML"
        )
        return
    
    await process_search_query(message, query)

@router.message(F.text & ~F.command)
async def handle_text_search(message: types.Message):
    """Обрабатывает текстовый поисковый запрос"""
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Запрос должен содержать минимум 2 символа")
        return
    
    await process_search_query(message, query)

async def process_search_query(message: types.Message, query: str):
    """Общая функция обработки поискового запроса"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                products = await perform_search(query, session)
                text, reply_markup = await build_search_response(products)
                
                await message.answer(
                    text,
                    reply_markup=reply_markup.as_markup() if reply_markup else None,
                    parse_mode="HTML"
                )

            except Exception as e:
                await message.answer("⚠️ Ошибка при поиске товаров")
                print(f"Search error: {type(e).__name__}: {e}")