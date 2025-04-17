from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from markupsafe import escape
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
from bot.database.models import Product, Category
from bot.database.session import engine

router = Router(name="search_handlers")
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

@router.message(Command("search"))
async def search_products(message: types.Message):
    try:
        query = escape(message.text.split(maxsplit=1)[1].strip())
    except IndexError:
        await message.answer(
            "🔍 Введите поисковый запрос:\n"
            "Пример: <code>/search тарелка</code>\n"
            "Или: <code>/search STK-001</code>",
            parse_mode="HTML"
        )
        return

    async with AsyncSession() as session:
        try:
            # Создаем асинхронную сессию
            async with session.begin():
                # Выполняем запрос
                stmt = select(Product).join(Category).where(
                    or_(
                        Product.name.ilike(f"%{query}%"),
                        Product.article.ilike(f"%{query}%"),
                        Category.name.ilike(f"%{query}%")
                    )
                ).limit(10)

                result = await session.execute(stmt)
                products = result.scalars().all()

                if not products:
                    await message.answer("🔍 Товары не найдены")
                    return

                # Формируем ответ
                response = ["🔍 Результаты поиска:"]
                for p in products:
                    # Получаем категорию для каждого товара
                    category = (await session.execute(
                        select(Category).where(Category.id == p.category_id)
                    )).scalar_one()
                    
                    response.append(
                        f"{hbold(p.name)} - {p.price} руб.\n"
                        f"Артикул: <code>{p.article}</code>\n"
                        f"Категория: {category.name}\n"
                    )

                response_text = "\n\n".join(response).encode('utf-8').decode('utf-8')
                await message.answer(response_text)
                

        except Exception as e:
            await message.answer("⚠️ Ошибка при поиске товаров")
            print(f"Search error: {e}")