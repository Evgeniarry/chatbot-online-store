from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Product, Order
from bot.database.session import AsyncSessionLocal  # Используем исправленную фабрику сессий

router = Router(name="order_handlers")

@router.message(Command("order"))
async def order_product(message: types.Message):
    try:
        article = message.text.split(maxsplit=1)[1].strip().upper()
    except IndexError:
        await message.answer(
            "ℹ️ Usage: /order <ARTICLE>\n"
            "Example: /order STK-001"
        )
        return

    async with AsyncSessionLocal() as session:
        # Находим товар по артикулу
        product = await session.execute(
            select(Product).where(Product.article == article))
        product = product.scalar_one_or_none()

        if not product:
            await message.answer(f"❌ Product with article {article} not found")
            return

        # Создаем заказ
        new_order = Order(
            user_id=message.from_user.id,
            product_id=product.id,
            quantity=1,
            status='created'
        )
        session.add(new_order)
        await session.commit()

        await message.answer(
            f"✅ Order created!\n"
            f"Product: {product.name}\n"
            f"Price: {product.price} RUB\n"
            f"Order #: {new_order.id}"
        )

@router.message(Command("history"))
async def order_history(message: types.Message):
    # Создаем новую сессию с явной привязкой
    async with AsyncSessionLocal() as session:
        try:
            # Явно начинаем транзакцию
            async with session.begin():
                # Загружаем заказы с связанными продуктами
                result = await session.execute(
                    select(Order)
                    .where(Order.user_id == message.from_user.id)
                    .order_by(Order.order_date.desc())
                    .limit(10)
                    .options(selectinload(Order.product))  # Жадная загрузка продукта
                )
                orders = result.scalars().all()

                if not orders:
                    await message.answer("📭 You have no orders yet")
                    return

                response = ["📋 Your last orders:"]
                for order in orders:
                    response.append(
                        f"🆔 #{order.id} {order.product.name}\n"
                        f"💰 {order.product.price} RUB\n"
                        f"📅 {order.order_date.strftime('%Y-%m-%d %H:%M')}\n"
                        f"🔹 Status: {order.status}"
                    )

                await message.answer("\n\n".join(response))
                
        except Exception as e:
            await message.answer("⚠️ Error loading order history")
            print(f"History error: {e}")