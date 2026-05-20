from datetime import datetime
from sqlalchemy.orm import Session

from models import Discount, DiscountScope, Listing


def create_discount(db: Session, shop_id: int, **kwargs) -> Discount:
    discount = Discount(shop_id=shop_id, **kwargs)
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def get_discount_by_id(db: Session, discount_id: int) -> Discount | None:
    return db.query(Discount).filter(Discount.id == discount_id).first()


def get_shop_discounts(db: Session, shop_id: int, only_active: bool = True):
    q = db.query(Discount).filter(Discount.shop_id == shop_id)
    if only_active:
        q = q.filter(Discount.is_active == True)
    return q.order_by(Discount.created_at.desc()).all()


def deactivate_discount(db: Session, discount_id: int) -> bool:
    d = get_discount_by_id(db, discount_id)
    if not d:
        return False
    d.is_active = False
    db.commit()
    return True


def get_best_discount_for_listing(db: Session, listing: Listing) -> Discount | None:
    """
    Найти лучшую (с максимальным процентом) активную скидку для товара.
    Учитывает все scope: product, category, shop.
    """
    if not listing.owner.shop:
        return None
    shop_id = listing.owner.shop.id

    now = datetime.utcnow()
    candidates = (
        db.query(Discount)
        .filter(
            Discount.shop_id == shop_id,
            Discount.is_active == True,
            Discount.starts_at <= now,
            Discount.ends_at >= now,
        )
        .all()
    )

    applicable = []
    for d in candidates:
        if d.scope == DiscountScope.shop:
            applicable.append(d)
        elif d.scope == DiscountScope.category and d.target_id == listing.category_id:
            applicable.append(d)
        elif d.scope == DiscountScope.product and d.target_id == listing.id:
            applicable.append(d)

    if not applicable:
        return None
    return max(applicable, key=lambda x: x.discount_percent)


def calculate_final_price(base_price: float, discount: Discount | None) -> float:
    if not discount:
        return base_price
    return round(base_price * (1 - discount.discount_percent / 100), 2)
