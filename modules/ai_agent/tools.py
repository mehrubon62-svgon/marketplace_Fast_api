"""
Инструменты (functions), которые AI-агент может вызывать.
Каждый инструмент имеет:
- описание схемы (для модели)
- реализацию (вызывается из agent.py)
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import Listing, Category, CartItem, Favorite, User


# -----------------------------
# Описание инструментов для LLM
# -----------------------------
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": (
                "Поиск товаров в маркетплейсе по ключевому слову, "
                "категории и диапазону цены. Возвращает список товаров."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос (название или часть описания товара)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Название категории (необязательно)",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Минимальная цена",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Максимальная цена",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Сколько товаров вернуть (по умолчанию 5, максимум 20)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_listing_details",
            "description": "Получить подробную информацию о конкретном товаре по его id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "integer",
                        "description": "ID товара",
                    }
                },
                "required": ["listing_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": (
                "Добавить товар в корзину текущего пользователя. "
                "Доступно только авторизованному пользователю."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "integer",
                        "description": "ID товара",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Количество (по умолчанию 1)",
                    },
                },
                "required": ["listing_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_favorites",
            "description": "Добавить товар в избранное текущего пользователя.",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "integer",
                        "description": "ID товара",
                    }
                },
                "required": ["listing_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "Получить список всех категорий маркетплейса.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# -----------------------------
# Реализации инструментов
# -----------------------------
def search_listings(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
):
    limit = min(max(limit or 5, 1), 20)
    q = db.query(Listing).filter(Listing.is_active == True)

    if query:
        like = f"%{query}%"
        q = q.filter(or_(Listing.title.ilike(like), Listing.description.ilike(like)))

    if category:
        cat = db.query(Category).filter(Category.name.ilike(f"%{category}%")).first()
        if cat:
            q = q.filter(Listing.category_id == cat.id)

    if min_price is not None:
        q = q.filter(Listing.price >= min_price)
    if max_price is not None:
        q = q.filter(Listing.price <= max_price)

    items = q.limit(limit).all()
    return [
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
            "quantity": l.quantity,
            "category_id": l.category_id,
            "image_url": l.image_url,
        }
        for l in items
    ]


def get_listing_details(db: Session, listing_id: int):
    l = db.query(Listing).filter(Listing.id == listing_id).first()
    if not l:
        return {"error": f"Товар с id={listing_id} не найден"}
    return {
        "id": l.id,
        "title": l.title,
        "description": l.description,
        "price": l.price,
        "quantity": l.quantity,
        "category_id": l.category_id,
        "owner_id": l.owner_id,
        "image_url": l.image_url,
        "is_active": l.is_active,
    }


def add_to_cart(db: Session, user: Optional[User], listing_id: int, quantity: int = 1):
    if not user:
        return {"error": "Действие доступно только авторизованным пользователям"}

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return {"error": f"Товар с id={listing_id} не найден"}

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == user.id, CartItem.listing_id == listing_id)
        .first()
    )
    if existing:
        existing.quantity += quantity
    else:
        existing = CartItem(user_id=user.id, listing_id=listing_id, quantity=quantity)
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return {
        "ok": True,
        "cart_item_id": existing.id,
        "listing_id": existing.listing_id,
        "quantity": existing.quantity,
    }


def add_to_favorites(db: Session, user: Optional[User], listing_id: int):
    if not user:
        return {"error": "Действие доступно только авторизованным пользователям"}

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return {"error": f"Товар с id={listing_id} не найден"}

    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
        .first()
    )
    if existing:
        return {"ok": True, "already_in_favorites": True}

    fav = Favorite(user_id=user.id, listing_id=listing_id)
    db.add(fav)
    db.commit()
    return {"ok": True, "favorite_id": fav.id}


def list_categories(db: Session):
    cats = db.query(Category).all()
    return [{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in cats]


# Маршрутизатор: имя -> функция
TOOL_FUNCTIONS = {
    "search_listings": search_listings,
    "get_listing_details": get_listing_details,
    "add_to_cart": add_to_cart,
    "add_to_favorites": add_to_favorites,
    "list_categories": list_categories,
}


def execute_tool(name: str, args: dict, db: Session, user: Optional[User]):
    """Вызвать инструмент по имени, передав нужные параметры."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Неизвестный инструмент: {name}"}

    # Инструменты которым нужен user
    if name in ("add_to_cart", "add_to_favorites"):
        return fn(db=db, user=user, **args)

    return fn(db=db, **args)
