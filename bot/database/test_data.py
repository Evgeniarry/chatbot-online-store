from bot.database.models import Category, Product
from bot.database.session import async_session

async def create_test_data():
    async with async_session() as session:
        # Создаем категории посуды
        categories = [
            Category(name="Тарелки"),
            Category(name="Сковороды"),
            Category(name="Столовые приборы"),
            Category(name="Стаканы и бокалы"),
            Category(name="Кастрюли")
        ]
        session.add_all(categories)
        await session.flush()  # Получаем ID категорий
        
        # Создаем товары
        products = [
            # Тарелки
            Product(
                name="Тарелка столовая керамическая 25см",
                price=890,
                article="TPL-001",
                category=categories[0]
            ),
            Product(
                name="Набор тарелок 6 предметов",
                price=4500,
                article="TPL-002",
                category=categories[0]
            ),
            
            # Сковороды
            Product(
                name="Сковорода антипригарная 28см",
                price=3200,
                article="SKV-001",
                category=categories[1]
            ),
            Product(
                name="Сковорода-гриль чугунная",
                price=5800,
                article="SKV-002",
                category=categories[1]
            ),
            
            # Столовые приборы
            Product(
                name="Набор столовых приборов 24 предмета",
                price=6700,
                article="PRI-001",
                category=categories[2]
            ),
            
            # Стаканы и бокалы
            Product(
                name="Набор бокалов для вина 6шт",
                price=3900,
                article="STK-001",
                category=categories[3]
            ),
            
            # Кастрюли
            Product(
                name="Кастрюля нержавеющая сталь 5л",
                price=4200,
                article="KST-001",
                category=categories[4]
            )
        ]
        session.add_all(products)
        await session.commit()
        
        print("✅ Тестовые данные для магазина посуды созданы")