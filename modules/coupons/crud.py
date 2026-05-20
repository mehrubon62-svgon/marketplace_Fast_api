from datetime import datetime
from sqlalchemy.orm import Session
from models import Coupon, CouponUsage


def create_coupon(db: Session, **kwargs) -> Coupon:
    coupon = Coupon(**kwargs)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def get_coupon_by_code(db: Session, code: str):
    return db.query(Coupon).filter(Coupon.code == code).first()


def get_all_coupons(db: Session):
    return db.query(Coupon).all()


def deactivate_coupon(db: Session, coupon_id: int) -> bool:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        return False
    coupon.is_active = False
    db.commit()
    return True


def is_coupon_valid(coupon: Coupon) -> tuple[bool, str | None]:
    if not coupon.is_active:
        return False, "Coupon is not active"
    if coupon.expires_at:
        expires = coupon.expires_at.replace(tzinfo=None) if coupon.expires_at.tzinfo else coupon.expires_at
        if expires < datetime.utcnow():
            return False, "Coupon expired"
    if coupon.max_uses and coupon.times_used >= coupon.max_uses:
        return False, "Coupon usage limit reached"
    return True, None


def calculate_discount(coupon: Coupon, order_total: float) -> float:
    if coupon.discount_percent:
        return round(order_total * coupon.discount_percent / 100.0, 2)
    if coupon.discount_amount:
        return min(coupon.discount_amount, order_total)
    return 0.0


def register_usage(db: Session, coupon: Coupon, user_id: int, order_id: int | None = None):
    usage = CouponUsage(coupon_id=coupon.id, user_id=user_id, order_id=order_id)
    coupon.times_used += 1
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage
