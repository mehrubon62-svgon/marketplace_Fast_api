from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Shop, ShopStatus, ShopReview, ShopFollower, Listing


def create_shop(db: Session, name: str, description: str | None, owner_id: int):
    shop = Shop(name=name, description=description, owner_id=owner_id)
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


def get_shop_by_id(db: Session, shop_id: int):
    return db.query(Shop).filter(Shop.id == shop_id).first()


def get_shop_by_owner(db: Session, owner_id: int):
    return db.query(Shop).filter(Shop.owner_id == owner_id).first()


def get_all_shops(db: Session):
    return db.query(Shop).all()


def get_pending_shops(db: Session):
    return db.query(Shop).filter(Shop.status == ShopStatus.pending).all()


def update_shop_status(db: Session, shop_id: int, status: ShopStatus):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if shop:
        shop.status = status
        db.commit()
        db.refresh(shop)
    return shop


def get_shop_detail(db: Session, shop_id: int):
    """Загружает магазин + агрегаты (рейтинг, кол-во подписчиков, товаров)."""
    shop = get_shop_by_id(db, shop_id)
    if not shop:
        return None

    rating_avg, reviews_count = (
        db.query(func.avg(ShopReview.rating), func.count(ShopReview.id))
        .filter(ShopReview.shop_id == shop_id)
        .first()
    )
    followers_count = (
        db.query(func.count(ShopFollower.id))
        .filter(ShopFollower.shop_id == shop_id)
        .scalar()
    )
    listings = (
        db.query(Listing)
        .filter(Listing.owner_id == shop.owner_id, Listing.is_active == True)
        .order_by(Listing.created_at.desc())
        .all()
    )

    return {
        "shop": shop,
        "rating_avg": round(float(rating_avg), 2) if rating_avg is not None else None,
        "reviews_count": reviews_count or 0,
        "followers_count": followers_count or 0,
        "listings": listings,
    }
