"""
Seed-данные для маркетплейса. Запуск: `python seed_data.py`.

Создаёт большой реалистичный набор:
- 30+ пользователей (1 админ, 8 продавцов, остальные покупатели)
- 8 магазинов с одобренным статусом
- Категории (с подкатегориями) и бренды
- ~120+ товаров с описаниями, ценами, изображениями, вариантами, тегами
- Скидки разного scope (product/category/shop)
- FlashSale с несколькими товарами
- Кошельки с пополнениями (админ топапит покупателей)
- Корзины, избранное, недавно просмотренные
- Заказы в разных статусах (pending/shipped/delivered) с корректными
  списаниями/зачислениями через кошельки
- Отзывы на товары (только для delivered заказов) и на магазины
- Чаты и сообщения, уведомления
- Купоны, способы доставки, баннеры, репорты
"""
import random
from datetime import datetime, timedelta, timezone

from models import (
    Base, engine, SessionLocal,
    RoleEnum, ShopStatus, OrderStatus, NotificationType, TxType, DiscountScope,
    User, Shop, Category, Listing, Review, Order, OrderItem, CartItem,
    Favorite, Brand, Tag, DeliveryMethod, Banner, Coupon, FlashSale,
    ProductImage, ProductVariant, Address, Notification, Chat, Message,
    OrderStatusHistory, ShopReview, ShopBanner, ShopFollower, RecentlyViewed,
    Report, ReportStatus, Wallet, WalletTransaction, Discount,
)
from modules.users.crud import create_user

Base.metadata.create_all(bind=engine)
db = SessionLocal()
random.seed(42)


def topup_wallet(user_id: int, amount: float, note: str = "Initial topup"):
    """Пополнить кошелёк пользователя через WalletTransaction."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.flush()
    wallet.balance += amount
    tx = WalletTransaction(
        wallet_id=wallet.id,
        amount=amount,
        tx_type=TxType.topup,
        description=note,
    )
    db.add(tx)
    return wallet


def seed():
    if db.query(User).first():
        print("Database already has data, skipping seed.")
        return

    print("Seeding data...")

    # =============== USERS ===============
    print("Creating users...")
    admin = create_user(db, "admin", "admin@marketplace.com", "admin123", RoleEnum.admin)

    sellers_data = [
        ("techworld", "tech@mail.com", "TechWorld", "Электроника и гаджеты"),
        ("fashionhub", "fashion@mail.com", "Fashion Hub", "Стильная одежда и аксессуары"),
        ("homestyle", "home@mail.com", "Home Style", "Всё для дома и уюта"),
        ("sportzone", "sport@mail.com", "Sport Zone", "Спортивные товары"),
        ("beautyshop", "beauty@mail.com", "Beauty Shop", "Косметика и парфюмерия"),
        ("kidsworld", "kids@mail.com", "Kids World", "Товары для детей"),
        ("bookstore", "books@mail.com", "Book Store", "Книги и канцелярия"),
        ("autoparts", "auto@mail.com", "Auto Parts", "Автозапчасти и аксессуары"),
    ]
    sellers = []
    shops = []
    for username, email, shop_name, shop_desc in sellers_data:
        u = create_user(db, username, email, "password123")
        sellers.append(u)
        shop = Shop(name=shop_name, description=shop_desc, status=ShopStatus.approved, owner_id=u.id)
        db.add(shop)
        shops.append(shop)

    db.flush()

    buyers_data = [
        ("alice", "alice@mail.com"), ("bob", "bob@mail.com"), ("carol", "carol@mail.com"),
        ("david", "david@mail.com"), ("eve", "eve@mail.com"), ("frank", "frank@mail.com"),
        ("grace", "grace@mail.com"), ("hank", "hank@mail.com"), ("ivy", "ivy@mail.com"),
        ("jack", "jack@mail.com"), ("kate", "kate@mail.com"), ("leo", "leo@mail.com"),
        ("mary", "mary@mail.com"), ("nick", "nick@mail.com"), ("olga", "olga@mail.com"),
        ("paul", "paul@mail.com"), ("quinn", "quinn@mail.com"), ("rita", "rita@mail.com"),
        ("sam", "sam@mail.com"), ("tina", "tina@mail.com"), ("uri", "uri@mail.com"),
        ("vera", "vera@mail.com"),
    ]
    buyers = [create_user(db, u, e, "password123") for u, e in buyers_data]

    db.commit()

    # =============== WALLETS: пополняем покупателям ===============
    print("Topping up wallets...")
    for buyer in buyers:
        amount = random.choice([2000, 3000, 5000, 7500, 10000, 15000])
        topup_wallet(buyer.id, amount, f"Пополнение администратором (#seed)")
    db.commit()

    # =============== CATEGORIES (с иерархией) ===============
    print("Creating categories...")
    cat_root = {
        "Электроника": ["Смартфоны", "Ноутбуки", "Аудио", "Аксессуары"],
        "Одежда": ["Мужская", "Женская", "Детская", "Обувь"],
        "Дом и сад": ["Кухня", "Освещение", "Текстиль", "Декор"],
        "Спорт": ["Фитнес", "Велосипеды", "Туризм", "Зимний спорт"],
        "Красота": ["Уход за кожей", "Макияж", "Парфюмерия"],
        "Дети": ["Игрушки", "Питание", "Одежда детская"],
        "Книги": ["Художественная", "Учебная", "Детская литература"],
        "Авто": ["Шины", "Масла", "Аксессуары авто"],
    }
    categories: dict[str, Category] = {}
    for parent_name, subs in cat_root.items():
        parent = Category(name=parent_name)
        db.add(parent)
        db.flush()
        categories[parent_name] = parent
        for sub in subs:
            child = Category(name=sub, parent_id=parent.id)
            db.add(child)
            db.flush()
            categories[sub] = child
    db.commit()

    # =============== BRANDS ===============
    print("Creating brands...")
    brand_names = [
        "Apple", "Samsung", "Xiaomi", "Sony", "Huawei", "Nike", "Adidas", "Puma",
        "Reebok", "Zara", "H&M", "Uniqlo", "IKEA", "Bosch", "Philips", "Dyson",
        "L'Oreal", "MAC", "Nivea", "Lego", "Mattel", "Penguin Books",
    ]
    brands = {}
    for name in brand_names:
        b = Brand(name=name)
        db.add(b)
        brands[name] = b
    db.commit()

    # =============== TAGS ===============
    print("Creating tags...")
    tag_names = [
        "новинка", "хит продаж", "распродажа", "premium", "эко", "ручная работа",
        "made in italy", "gaming", "vintage", "органик", "limited edition",
        "семейный", "профессиональный", "для дома", "подарок", "лето", "зима",
    ]
    tags = {}
    for name in tag_names:
        t = Tag(name=name)
        db.add(t)
        tags[name] = t
    db.commit()

    # =============== LISTINGS (товары) ===============
    print("Creating listings...")
    products_data = [
        # TechWorld
        (0, "Смартфоны", "Apple", ["новинка", "premium"], "iPhone 15 Pro", "Топовый смартфон Apple A17 Pro, 256GB, ProMotion дисплей", 999.0, 25, "https://picsum.photos/seed/iphone15/600/600"),
        (0, "Смартфоны", "Samsung", ["хит продаж"], "Samsung Galaxy S24 Ultra", "Флагман Samsung с S Pen, 512GB, AI features", 1199.0, 18, "https://picsum.photos/seed/galaxys24/600/600"),
        (0, "Смартфоны", "Xiaomi", ["распродажа"], "Xiaomi 14 Pro", "Камера Leica, Snapdragon 8 Gen 3, 256GB", 799.0, 30, "https://picsum.photos/seed/xiaomi14/600/600"),
        (0, "Смартфоны", "Huawei", [], "Huawei Pura 70 Pro", "Камера Ultra Sense, 12+512GB", 899.0, 12, "https://picsum.photos/seed/huawei70/600/600"),
        (0, "Ноутбуки", "Apple", ["premium"], "MacBook Pro 14 M3", "Apple M3 Pro, 16GB, 512GB SSD, Liquid Retina XDR", 1999.0, 10, "https://picsum.photos/seed/mbpro14/600/600"),
        (0, "Ноутбуки", "Apple", ["новинка"], "MacBook Air 13 M3", "Тонкий и лёгкий, M3, 8GB, 256GB", 1299.0, 15, "https://picsum.photos/seed/mbair13/600/600"),
        (0, "Ноутбуки", "Samsung", [], "Samsung Galaxy Book4 Pro", "Intel Core Ultra 7, 16GB, 1TB, OLED 3K", 1499.0, 8, "https://picsum.photos/seed/galaxybook4/600/600"),
        (0, "Аудио", "Apple", ["хит продаж"], "AirPods Pro 2", "Активное шумоподавление, USB-C", 249.0, 50, "https://picsum.photos/seed/airpodspro/600/600"),
        (0, "Аудио", "Sony", ["premium"], "Sony WH-1000XM5", "Беспроводные наушники с лучшим в индустрии шумоподавлением", 399.0, 20, "https://picsum.photos/seed/sonyxm5/600/600"),
        (0, "Аудио", "Xiaomi", ["распродажа"], "Xiaomi Redmi Buds 5 Pro", "Hi-Res, 38 ч работы", 79.0, 100, "https://picsum.photos/seed/redmibuds/600/600"),
        (0, "Аксессуары", "Apple", [], "Apple Watch Ultra 2", "Титан, 49мм, GPS+Cellular", 799.0, 14, "https://picsum.photos/seed/applewatchultra/600/600"),
        (0, "Аксессуары", "Samsung", [], "Galaxy Buds 3 Pro", "Galaxy AI, 24-bit Hi-Fi", 249.0, 35, "https://picsum.photos/seed/galaxybuds3/600/600"),
        (0, "Аксессуары", "Xiaomi", [], "Xiaomi Mi Band 8", "Фитнес-трекер с AMOLED дисплеем", 49.0, 200, "https://picsum.photos/seed/miband8/600/600"),
        (0, "Аксессуары", "Bosch", [], "Bosch Smart Home Hub", "Центр умного дома Bosch", 199.0, 22, "https://picsum.photos/seed/boschhub/600/600"),

        # Fashion Hub
        (1, "Мужская", "Nike", ["хит продаж"], "Nike Sportswear Tech Fleece Hoodie", "Мужская толстовка из премиум-флиса", 129.0, 60, "https://picsum.photos/seed/nikehoodie/600/600"),
        (1, "Мужская", "Adidas", [], "Adidas Originals Trefoil T-Shirt", "Классическая футболка с логотипом", 39.0, 200, "https://picsum.photos/seed/adidastee/600/600"),
        (1, "Мужская", "Zara", [], "Zara Slim-Fit Wool Suit", "Шерстяной костюм узкого кроя", 299.0, 25, "https://picsum.photos/seed/zarasuit/600/600"),
        (1, "Женская", "Zara", ["новинка"], "Zara Floral Midi Dress", "Платье миди с цветочным принтом", 89.0, 80, "https://picsum.photos/seed/zaradress/600/600"),
        (1, "Женская", "H&M", ["распродажа"], "H&M Knit Sweater", "Уютный вязаный свитер", 49.0, 150, "https://picsum.photos/seed/hmsweater/600/600"),
        (1, "Женская", "Uniqlo", [], "Uniqlo Heattech Crew Neck", "Тёплое термобельё", 19.0, 300, "https://picsum.photos/seed/uniqloheattech/600/600"),
        (1, "Обувь", "Nike", ["хит продаж"], "Nike Air Max 270", "Кроссовки Air Max с максимальной амортизацией", 159.0, 70, "https://picsum.photos/seed/airmax270/600/600"),
        (1, "Обувь", "Adidas", [], "Adidas Ultraboost 22", "Беговые кроссовки с технологией Boost", 189.0, 45, "https://picsum.photos/seed/ultraboost/600/600"),
        (1, "Обувь", "Puma", ["распродажа"], "Puma RS-X", "Стильные кроссовки в винтажном стиле", 99.0, 90, "https://picsum.photos/seed/pumarsx/600/600"),
        (1, "Обувь", "Reebok", [], "Reebok Classic Leather", "Классические белые кроссовки", 79.0, 110, "https://picsum.photos/seed/reebokclassic/600/600"),
        (1, "Детская", "H&M", [], "H&M Kids Denim Jacket", "Детская джинсовая куртка", 35.0, 80, "https://picsum.photos/seed/hmkidsjacket/600/600"),

        # Home Style
        (2, "Кухня", "Bosch", [], "Bosch Series 4 Dishwasher", "Посудомоечная машина 60 см", 599.0, 8, "https://picsum.photos/seed/boschdishwasher/600/600"),
        (2, "Кухня", "Philips", [], "Philips Airfryer XXL", "Аэрогриль 7,3 л", 249.0, 30, "https://picsum.photos/seed/philipsairfryer/600/600"),
        (2, "Кухня", "Dyson", ["premium"], "Dyson V15 Detect", "Беспроводной пылесос с лазерной подсветкой", 749.0, 12, "https://picsum.photos/seed/dysonv15/600/600"),
        (2, "Освещение", "IKEA", [], "IKEA TRÅDFRI LED bulb", "Умная лампочка E27, 9W", 9.99, 500, "https://picsum.photos/seed/ikealamp/600/600"),
        (2, "Освещение", "Philips", [], "Philips Hue Starter Kit", "Стартовый набор умного освещения", 199.0, 20, "https://picsum.photos/seed/huestarter/600/600"),
        (2, "Текстиль", "IKEA", ["для дома"], "IKEA DVALA Bedding Set", "Постельное бельё 200x220", 49.0, 100, "https://picsum.photos/seed/ikeabedding/600/600"),
        (2, "Декор", "IKEA", ["эко"], "IKEA SOLLERÖN Outdoor Sofa", "Садовый диван из ротанга", 399.0, 5, "https://picsum.photos/seed/ikeasofa/600/600"),
        (2, "Кухня", "IKEA", [], "IKEA 365+ Frying Pan", "Сковорода с антипригарным покрытием 28см", 39.0, 80, "https://picsum.photos/seed/ikeapan/600/600"),

        # Sport Zone
        (3, "Фитнес", "Nike", [], "Nike Yoga Mat", "Профессиональный коврик для йоги", 49.0, 60, "https://picsum.photos/seed/nikeyoga/600/600"),
        (3, "Фитнес", "Adidas", [], "Adidas Power Gym Bag", "Спортивная сумка 20л", 39.0, 100, "https://picsum.photos/seed/adidasbag/600/600"),
        (3, "Фитнес", "Reebok", ["профессиональный"], "Reebok Adjustable Dumbbell Set", "Гантели регулируемые 2x24 кг", 299.0, 18, "https://picsum.photos/seed/reebokdumbbells/600/600"),
        (3, "Велосипеды", None, [], "Trek FX 3 Disc", "Городской велосипед с дисковыми тормозами", 899.0, 8, "https://picsum.photos/seed/trekfx3/600/600"),
        (3, "Туризм", None, ["limited edition"], "MSR Hubba Hubba 2-Person Tent", "Палатка двухместная ультралёгкая", 449.0, 15, "https://picsum.photos/seed/msrtent/600/600"),
        (3, "Зимний спорт", None, [], "Salomon QST 99 Skis", "Универсальные горные лыжи 178см", 599.0, 10, "https://picsum.photos/seed/salomonskis/600/600"),
        (3, "Фитнес", "Nike", ["хит продаж"], "Nike Pro Compression Shorts", "Компрессионные шорты", 39.0, 200, "https://picsum.photos/seed/nikeshorts/600/600"),

        # Beauty Shop
        (4, "Уход за кожей", "L'Oreal", ["хит продаж"], "L'Oreal Revitalift Serum", "Сыворотка с гиалуроновой кислотой 30мл", 29.99, 200, "https://picsum.photos/seed/lorealserum/600/600"),
        (4, "Уход за кожей", "Nivea", [], "Nivea Q10 Day Cream", "Дневной крем против морщин", 14.99, 300, "https://picsum.photos/seed/niveacream/600/600"),
        (4, "Уход за кожей", "Nivea", [], "Nivea Sun SPF50", "Солнцезащитный крем 200мл", 11.99, 400, "https://picsum.photos/seed/niveasun/600/600"),
        (4, "Макияж", "MAC", ["premium"], "MAC Ruby Woo Lipstick", "Культовая красная помада", 24.0, 150, "https://picsum.photos/seed/macruby/600/600"),
        (4, "Макияж", "L'Oreal", [], "L'Oreal Telescopic Mascara", "Тушь с эффектом удлинения", 12.99, 250, "https://picsum.photos/seed/lorealmascara/600/600"),
        (4, "Парфюмерия", None, ["premium", "limited edition"], "Chanel No. 5 EDP 50ml", "Легендарный аромат Chanel", 165.0, 30, "https://picsum.photos/seed/chanel5/600/600"),
        (4, "Парфюмерия", None, [], "Dior Sauvage 100ml", "Мужской аромат Dior", 145.0, 40, "https://picsum.photos/seed/diorsauvage/600/600"),

        # Kids World
        (5, "Игрушки", "Lego", ["хит продаж", "семейный"], "LEGO City Police Station", "Конструктор Полицейский участок 743 детали", 99.99, 50, "https://picsum.photos/seed/legopolice/600/600"),
        (5, "Игрушки", "Lego", ["новинка"], "LEGO Star Wars Millennium Falcon", "Эпический корабль 1351 деталей", 169.99, 20, "https://picsum.photos/seed/legofalcon/600/600"),
        (5, "Игрушки", "Mattel", [], "Hot Wheels 50-pack Cars", "Набор из 50 машинок", 49.99, 80, "https://picsum.photos/seed/hotwheels/600/600"),
        (5, "Питание", None, ["эко", "органик"], "HiPP Organic Baby Cereal", "Органическая каша 200г", 5.99, 500, "https://picsum.photos/seed/hippcereal/600/600"),
        (5, "Одежда детская", "H&M", [], "H&M Kids Pajama Set", "Пижама 100% хлопок", 19.99, 150, "https://picsum.photos/seed/hmpyjama/600/600"),

        # Book Store
        (6, "Художественная", "Penguin Books", [], "1984 by George Orwell", "Классическая антиутопия", 9.99, 300, "https://picsum.photos/seed/1984/600/600"),
        (6, "Художественная", "Penguin Books", ["хит продаж"], "Atomic Habits by James Clear", "Бестселлер о привычках", 14.99, 250, "https://picsum.photos/seed/atomichabits/600/600"),
        (6, "Учебная", None, [], "Python Crash Course 3rd Ed", "Учебник по Python для начинающих", 29.99, 100, "https://picsum.photos/seed/pythonbook/600/600"),
        (6, "Учебная", None, ["профессиональный"], "Designing Data-Intensive Applications", "Книга для backend-разработчиков", 49.99, 80, "https://picsum.photos/seed/dddapps/600/600"),
        (6, "Детская литература", None, [], "The Very Hungry Caterpillar", "Классическая детская книга", 7.99, 200, "https://picsum.photos/seed/caterpillar/600/600"),

        # Auto Parts
        (7, "Шины", None, [], "Michelin Pilot Sport 4 225/45R17", "Летние шины премиум", 189.0, 40, "https://picsum.photos/seed/michelin/600/600"),
        (7, "Шины", None, ["зима"], "Nokian Hakkapeliitta R5 215/55R17", "Зимние шины", 219.0, 25, "https://picsum.photos/seed/nokian/600/600"),
        (7, "Масла", None, [], "Mobil 1 5W-30 4L", "Синтетическое моторное масло", 49.99, 100, "https://picsum.photos/seed/mobiloil/600/600"),
        (7, "Аксессуары авто", "Bosch", [], "Bosch Wiper Blades Aerotwin", "Дворники бескаркасные", 29.99, 200, "https://picsum.photos/seed/boschwipers/600/600"),
    ]

    listings: list[Listing] = []
    for (shop_idx, cat_name, brand_name, tag_list, title, desc, price, qty, img) in products_data:
        shop = shops[shop_idx]
        cat = categories.get(cat_name)
        brand = brands.get(brand_name) if brand_name else None
        listing = Listing(
            title=title,
            description=desc,
            price=price,
            quantity=qty,
            image_url=img,
            category_id=cat.id,
            owner_id=shop.owner_id,
            brand_id=brand.id if brand else None,
        )
        for t_name in tag_list:
            if t_name in tags:
                listing.tags.append(tags[t_name])
        db.add(listing)
        listings.append(listing)
    db.commit()
    for l in listings:
        db.refresh(l)

    # Дополнительные изображения и варианты
    print("Adding product images and variants...")
    for l in listings:
        # 1-3 доп изображения
        for i in range(random.randint(1, 3)):
            db.add(ProductImage(
                listing_id=l.id,
                url=f"https://picsum.photos/seed/{l.id}-{i}/600/600",
                is_primary=False,
                sort_order=i + 1,
            ))
        # У одежды и обуви — варианты по размеру
        if any(c in (l.category.name if l.category else "") for c in ("Мужская", "Женская", "Обувь", "Детская")):
            for size in random.sample(["XS", "S", "M", "L", "XL", "36", "38", "40", "42", "44"], 3):
                db.add(ProductVariant(
                    listing_id=l.id,
                    name=f"Размер {size}",
                    price=l.price,
                    quantity=random.randint(5, 30),
                    sku=f"SKU-{l.id}-{size}",
                ))
    db.commit()

    # =============== DISCOUNTS ===============
    print("Creating discounts...")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    one_month_later = now + timedelta(days=30)

    # Скидка на весь магазин Beauty Shop
    db.add(Discount(
        shop_id=shops[4].id,
        scope=DiscountScope.shop,
        target_id=None,
        discount_percent=15.0,
        starts_at=now - timedelta(days=2),
        ends_at=one_month_later,
    ))
    # Скидка на категорию Смартфоны
    db.add(Discount(
        shop_id=shops[0].id,
        scope=DiscountScope.category,
        target_id=categories["Смартфоны"].id,
        discount_percent=10.0,
        starts_at=now - timedelta(days=5),
        ends_at=one_month_later,
    ))
    # Скидка на категорию Обувь
    db.add(Discount(
        shop_id=shops[1].id,
        scope=DiscountScope.category,
        target_id=categories["Обувь"].id,
        discount_percent=20.0,
        starts_at=now - timedelta(days=1),
        ends_at=one_month_later,
    ))
    # Скидки на отдельные топ-товары
    top_listings = [l for l in listings if "хит продаж" in [t.name for t in l.tags]]
    for l in random.sample(top_listings, min(5, len(top_listings))):
        # ищем магазин товара
        shop = next(s for s in shops if s.owner_id == l.owner_id)
        db.add(Discount(
            shop_id=shop.id,
            scope=DiscountScope.product,
            target_id=l.id,
            discount_percent=random.choice([25.0, 30.0, 35.0]),
            starts_at=now - timedelta(days=3),
            ends_at=now + timedelta(days=14),
        ))
    db.commit()

    # =============== TAGS уже добавлены через relationship ===============

    # =============== DELIVERY METHODS ===============
    print("Creating delivery methods...")
    delivery_methods = [
        DeliveryMethod(name="Самовывоз", price=0, estimated_days=1),
        DeliveryMethod(name="Курьер по городу", price=5.99, estimated_days=2),
        DeliveryMethod(name="СДЭК", price=9.99, estimated_days=4),
        DeliveryMethod(name="Почта России", price=3.99, estimated_days=10),
        DeliveryMethod(name="Express International", price=29.99, estimated_days=2),
    ]
    for dm in delivery_methods:
        db.add(dm)
    db.commit()

    # =============== COUPONS ===============
    print("Creating coupons...")
    coupons = [
        Coupon(code="WELCOME10", discount_percent=10, max_uses=100,
               expires_at=datetime.utcnow() + timedelta(days=30)),
        Coupon(code="SUMMER20", discount_percent=20, max_uses=50,
               expires_at=datetime.utcnow() + timedelta(days=60)),
        Coupon(code="BLACKFRIDAY", discount_percent=30, max_uses=200,
               expires_at=datetime.utcnow() + timedelta(days=90)),
        Coupon(code="FIRSTORDER", discount_amount=15.00, max_uses=500,
               expires_at=datetime.utcnow() + timedelta(days=120)),
        Coupon(code="VIP50", discount_percent=50, max_uses=10,
               expires_at=datetime.utcnow() + timedelta(days=14)),
    ]
    for c in coupons:
        db.add(c)
    db.commit()

    # =============== ADDRESSES ===============
    print("Creating addresses...")
    cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Минск", "Алматы"]
    streets = ["ул. Ленина 12", "пр-т Мира 45", "ул. Пушкина 8", "ул. Гагарина 22", "ул. Советская 5"]
    for buyer in buyers:
        for i in range(random.randint(1, 2)):
            db.add(Address(
                user_id=buyer.id,
                full_name=buyer.username.title(),
                phone=f"+7900{random.randint(1000000, 9999999)}",
                country=random.choice(["Россия", "Беларусь", "Казахстан"]),
                city=random.choice(cities),
                street=random.choice(streets),
                postal_code=str(random.randint(100000, 999999)),
                is_default=(i == 0),
            ))
    db.commit()

    # =============== CART ITEMS ===============
    print("Adding items to carts...")
    for buyer in buyers[:10]:
        for _ in range(random.randint(1, 3)):
            l = random.choice(listings)
            if l.owner_id == buyer.id:
                continue
            db.add(CartItem(user_id=buyer.id, listing_id=l.id, quantity=random.randint(1, 3)))
    db.commit()

    # =============== FAVORITES ===============
    print("Adding favorites...")
    for buyer in buyers:
        favs = random.sample(listings, k=random.randint(2, 6))
        for l in favs:
            if l.owner_id == buyer.id:
                continue
            db.add(Favorite(user_id=buyer.id, listing_id=l.id))
    db.commit()

    # =============== RECENTLY VIEWED ===============
    print("Adding recently viewed...")
    for buyer in buyers:
        for l in random.sample(listings, k=random.randint(3, 10)):
            db.add(RecentlyViewed(
                user_id=buyer.id,
                listing_id=l.id,
                viewed_at=datetime.utcnow() - timedelta(hours=random.randint(0, 240)),
            ))
    db.commit()

    # =============== ORDERS (с транзакциями кошельков) ===============
    print("Creating orders with wallet transactions...")
    delivery_methods_db = db.query(DeliveryMethod).all()

    def calc_discount_price(listing, shop_id):
        """Применяет лучшую активную скидку магазина к товару."""
        active_discounts = db.query(Discount).filter(
            Discount.shop_id == shop_id,
            Discount.is_active == True,
            Discount.starts_at <= datetime.utcnow(),
            Discount.ends_at >= datetime.utcnow(),
        ).all()
        best = 0.0
        for d in active_discounts:
            if d.scope == DiscountScope.shop:
                best = max(best, d.discount_percent)
            elif d.scope == DiscountScope.category and d.target_id == listing.category_id:
                best = max(best, d.discount_percent)
            elif d.scope == DiscountScope.product and d.target_id == listing.id:
                best = max(best, d.discount_percent)
        if best > 0:
            return round(listing.price * (1 - best / 100), 2)
        return listing.price

    statuses_to_create = (
        [OrderStatus.delivered] * 15 +
        [OrderStatus.shipped] * 8 +
        [OrderStatus.confirmed] * 4 +
        [OrderStatus.pending] * 5 +
        [OrderStatus.cancelled] * 2
    )
    random.shuffle(statuses_to_create)

    orders_created = []
    for status in statuses_to_create:
        buyer = random.choice(buyers)
        # 1-3 товара в заказе
        chosen = random.sample(listings, k=random.randint(1, 3))
        # Группируем по продавцу — для простоты берём первого
        seller_id = chosen[0].owner_id
        chosen = [c for c in chosen if c.owner_id == seller_id]

        # Адрес
        addr = db.query(Address).filter(Address.user_id == buyer.id, Address.is_default == True).first()
        addr_str = f"{addr.country}, {addr.city}, {addr.street}" if addr else "Москва, ул. Ленина 1"

        # Считаем сумму с учётом скидок
        seller_shop = next(s for s in shops if s.owner_id == seller_id)
        items_data = []
        subtotal = 0.0
        for l in chosen:
            qty = random.randint(1, 2)
            unit_price = calc_discount_price(l, seller_shop.id)
            items_data.append((l, qty, unit_price))
            subtotal += unit_price * qty

        delivery = random.choice(delivery_methods_db)
        total = round(subtotal + delivery.price, 2)

        # Проверяем баланс
        wallet = db.query(Wallet).filter(Wallet.user_id == buyer.id).first()
        if wallet.balance < total:
            continue

        # Создаём заказ
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 60))
        order = Order(
            buyer_id=buyer.id,
            seller_id=seller_id,
            status=status,
            total_price=total,
            address=addr_str,
            delivery_method_id=delivery.id,
            created_at=created_at,
        )
        db.add(order)
        db.flush()

        for l, qty, unit_price in items_data:
            db.add(OrderItem(order_id=order.id, listing_id=l.id, quantity=qty, price=unit_price))
            l.quantity = max(0, l.quantity - qty)

        # История статусов
        db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.pending, changed_at=created_at, note="Order created"))
        if status in (OrderStatus.confirmed, OrderStatus.shipped, OrderStatus.delivered):
            db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.confirmed, changed_at=created_at + timedelta(hours=2)))
        if status in (OrderStatus.shipped, OrderStatus.delivered):
            db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.shipped, changed_at=created_at + timedelta(days=1)))
        if status == OrderStatus.delivered:
            db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.delivered, changed_at=created_at + timedelta(days=3)))
        if status == OrderStatus.cancelled:
            db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.cancelled, changed_at=created_at + timedelta(hours=5), note="Buyer cancelled"))

        # Финансовые транзакции (если не отменён)
        if status != OrderStatus.cancelled:
            wallet.balance -= total
            db.add(WalletTransaction(
                wallet_id=wallet.id,
                amount=-total,
                tx_type=TxType.order_payment,
                description=f"Оплата заказа #{order.id}",
                order_id=order.id,
                created_at=created_at,
            ))
            seller_wallet = db.query(Wallet).filter(Wallet.user_id == seller_id).first()
            if not seller_wallet:
                seller_wallet = Wallet(user_id=seller_id, balance=0.0)
                db.add(seller_wallet)
                db.flush()
            seller_wallet.balance += subtotal
            db.add(WalletTransaction(
                wallet_id=seller_wallet.id,
                amount=subtotal,
                tx_type=TxType.order_income,
                description=f"Доход от заказа #{order.id}",
                order_id=order.id,
                created_at=created_at,
            ))

        orders_created.append(order)
    db.commit()

    print(f"  Created {len(orders_created)} orders")

    # =============== REVIEWS (только для delivered) ===============
    print("Creating product reviews...")
    delivered_orders = [o for o in orders_created if o.status == OrderStatus.delivered]
    review_comments = [
        "Отличный товар, рекомендую!", "Качество супер, как и описано.",
        "Доставка быстрая, всё работает.", "Хорошая цена за такое качество.",
        "Покупаю не первый раз.", "Полностью соответствует описанию.",
        "Превзошёл ожидания!", "Нормально, но могло быть лучше.",
        "Рекомендую к покупке.", "Прекрасный подарок.",
    ]
    for order in delivered_orders:
        for item in order.items:
            if random.random() < 0.7:  # 70% оставляют отзыв
                # Проверяем что ещё не оставлял
                existing = db.query(Review).filter(
                    Review.listing_id == item.listing_id,
                    Review.author_id == order.buyer_id,
                    Review.order_id == order.id,
                ).first()
                if not existing:
                    db.add(Review(
                        rating=random.randint(3, 5),
                        comment=random.choice(review_comments),
                        listing_id=item.listing_id,
                        author_id=order.buyer_id,
                        order_id=order.id,
                        created_at=order.created_at + timedelta(days=4),
                    ))
    db.commit()

    # =============== SHOP REVIEWS ===============
    print("Creating shop reviews...")
    shop_review_comments = [
        "Хороший магазин, быстрая доставка.", "Все товары соответствуют описанию.",
        "Понравилось обслуживание.", "Качественные товары, рекомендую.",
        "Удобный сайт, выгодные цены.", "Магазин с большим выбором.",
    ]
    for shop in shops:
        for buyer in random.sample(buyers, k=random.randint(2, 5)):
            db.add(ShopReview(
                shop_id=shop.id,
                author_id=buyer.id,
                rating=random.randint(3, 5),
                comment=random.choice(shop_review_comments),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            ))
    db.commit()

    # =============== SHOP FOLLOWERS ===============
    print("Creating shop followers...")
    for shop in shops:
        for buyer in random.sample(buyers, k=random.randint(3, 12)):
            if not db.query(ShopFollower).filter(
                ShopFollower.shop_id == shop.id, ShopFollower.user_id == buyer.id
            ).first():
                db.add(ShopFollower(shop_id=shop.id, user_id=buyer.id))
    db.commit()

    # =============== SHOP BANNERS ===============
    print("Creating shop banners...")
    for i, shop in enumerate(shops):
        db.add(ShopBanner(
            shop_id=shop.id,
            image_url=f"https://picsum.photos/seed/banner-{shop.id}/1200/400",
            title=f"Распродажа в {shop.name}",
            is_active=True,
        ))
    db.commit()

    # =============== CHATS ===============
    print("Creating chats and messages...")
    chat_msgs = [
        "Здравствуйте! У вас есть в наличии?",
        "Добрый день, да, есть.",
        "Когда сможете отправить?",
        "Сегодня вечером.",
        "Спасибо!",
        "А есть скидка?",
        "Сейчас действует акция -10%.",
        "Отлично, оформляю заказ.",
        "Хорошо, ждём оплаты.",
    ]
    for shop in shops:
        for buyer in random.sample(buyers, k=random.randint(2, 5)):
            a, b = sorted([shop.owner_id, buyer.id])
            chat = Chat(user_a_id=a, user_b_id=b)
            db.add(chat)
            db.flush()
            for i in range(random.randint(2, 6)):
                sender = random.choice([a, b])
                db.add(Message(
                    chat_id=chat.id,
                    sender_id=sender,
                    text=random.choice(chat_msgs),
                    is_read=random.choice([True, False]),
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
                ))
    db.commit()

    # =============== NOTIFICATIONS ===============
    print("Creating notifications...")
    for buyer in buyers:
        for _ in range(random.randint(1, 4)):
            ntype = random.choice([NotificationType.order, NotificationType.system, NotificationType.wallet])
            titles = {
                NotificationType.order: ("Обновление заказа", "Статус вашего заказа изменился"),
                NotificationType.system: ("Добро пожаловать!", "Спасибо что выбрали наш маркетплейс"),
                NotificationType.wallet: ("Баланс пополнен", "Ваш баланс обновлён"),
            }
            title, body = titles[ntype]
            db.add(Notification(
                user_id=buyer.id,
                type=ntype,
                title=title,
                body=body,
                is_read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 168)),
            ))
    db.commit()

    # =============== BANNERS (маркетинговые) ===============
    print("Creating marketing banners...")
    for i in range(5):
        db.add(Banner(
            image_url=f"https://picsum.photos/seed/promo-{i}/1200/400",
            title=random.choice(["Black Friday", "Новая коллекция", "Распродажа сезона", "Скидки до 70%"]),
            link="/listings",
            is_active=True,
            sort_order=i,
        ))
    db.commit()

    # =============== FLASH SALES ===============
    print("Creating flash sales...")
    fs1 = FlashSale(
        title="Электроника-распродажа",
        discount_percent=25.0,
        starts_at=datetime.utcnow() - timedelta(hours=1),
        ends_at=datetime.utcnow() + timedelta(days=3),
    )
    fs1.listings = [l for l in listings if "Смартфон" in l.title or "MacBook" in l.title][:5]
    db.add(fs1)

    fs2 = FlashSale(
        title="Мега скидки на обувь",
        discount_percent=30.0,
        starts_at=datetime.utcnow() - timedelta(hours=5),
        ends_at=datetime.utcnow() + timedelta(days=7),
    )
    fs2.listings = [l for l in listings if "Обувь" == (l.category.name if l.category else "")][:4]
    db.add(fs2)
    db.commit()

    # =============== REPORTS ===============
    print("Creating reports...")
    for _ in range(5):
        db.add(Report(
            reporter_id=random.choice(buyers).id,
            target_type=random.choice(["listing", "shop", "review"]),
            target_id=random.choice(listings).id,
            reason=random.choice([
                "Несоответствие описанию", "Спам", "Некорректная цена",
                "Подозрительный продавец", "Дубликат",
            ]),
            status=random.choice([ReportStatus.open, ReportStatus.reviewing, ReportStatus.resolved]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 14)),
        ))
    db.commit()

    print()
    print("=" * 60)
    print("  SEED COMPLETED")
    print("=" * 60)
    print(f"Users:        {db.query(User).count()}  (1 admin, {len(sellers)} sellers, {len(buyers)} buyers)")
    print(f"Shops:        {db.query(Shop).count()}")
    print(f"Categories:   {db.query(Category).count()}")
    print(f"Brands:       {db.query(Brand).count()}")
    print(f"Tags:         {db.query(Tag).count()}")
    print(f"Listings:     {db.query(Listing).count()}")
    print(f"Variants:     {db.query(ProductVariant).count()}")
    print(f"Discounts:    {db.query(Discount).count()}")
    print(f"FlashSales:   {db.query(FlashSale).count()}")
    print(f"Coupons:      {db.query(Coupon).count()}")
    print(f"Wallets:      {db.query(Wallet).count()}  (txs: {db.query(WalletTransaction).count()})")
    print(f"Orders:       {db.query(Order).count()}")
    print(f"OrderItems:   {db.query(OrderItem).count()}")
    print(f"Reviews:      {db.query(Review).count()}")
    print(f"ShopReviews:  {db.query(ShopReview).count()}")
    print(f"Followers:    {db.query(ShopFollower).count()}")
    print(f"Cart items:   {db.query(CartItem).count()}")
    print(f"Favorites:    {db.query(Favorite).count()}")
    print(f"Addresses:    {db.query(Address).count()}")
    print(f"Chats:        {db.query(Chat).count()}  (msgs: {db.query(Message).count()})")
    print(f"Notifications:{db.query(Notification).count()}")
    print(f"Banners:      {db.query(Banner).count()}")
    print(f"Reports:      {db.query(Report).count()}")
    print()
    print("Login as admin: admin / admin123")
    print("Login as seller: techworld / password123 (or fashionhub, homestyle, ...)")
    print("Login as buyer: alice / password123 (or bob, carol, ...)")


if __name__ == "__main__":
    try:
        seed()
    finally:
        db.close()
