from sqlalchemy.orm import Session
from models import ShopReview, ShopBanner, ShopFollower, Shop


# ---- Reviews ----
def create_shop_review(db: Session, shop_id: int, author_id: int, rating: int, comment: str | None) -> ShopReview:
    r = ShopReview(shop_id=shop_id, author_id=author_id, rating=rating, comment=comment)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_shop_reviews(db: Session, shop_id: int):
    return db.query(ShopReview).filter(ShopReview.shop_id == shop_id).order_by(ShopReview.created_at.desc()).all()


def delete_shop_review(db: Session, review_id: int) -> bool:
    r = db.query(ShopReview).filter(ShopReview.id == review_id).first()
    if not r:
        return False
    db.delete(r)
    db.commit()
    return True


# ---- Banners ----
def create_shop_banner(db: Session, shop_id: int, **kwargs) -> ShopBanner:
    b = ShopBanner(shop_id=shop_id, **kwargs)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def get_shop_banners(db: Session, shop_id: int):
    return db.query(ShopBanner).filter(ShopBanner.shop_id == shop_id).all()


def delete_shop_banner(db: Session, banner_id: int) -> ShopBanner | None:
    b = db.query(ShopBanner).filter(ShopBanner.id == banner_id).first()
    if not b:
        return None
    db.delete(b)
    db.commit()
    return b


# ---- Followers ----
def follow_shop(db: Session, shop_id: int, user_id: int) -> ShopFollower:
    existing = (
        db.query(ShopFollower)
        .filter(ShopFollower.shop_id == shop_id, ShopFollower.user_id == user_id)
        .first()
    )
    if existing:
        return existing
    f = ShopFollower(shop_id=shop_id, user_id=user_id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def unfollow_shop(db: Session, shop_id: int, user_id: int) -> bool:
    f = (
        db.query(ShopFollower)
        .filter(ShopFollower.shop_id == shop_id, ShopFollower.user_id == user_id)
        .first()
    )
    if not f:
        return False
    db.delete(f)
    db.commit()
    return True


def get_shop_followers(db: Session, shop_id: int):
    return db.query(ShopFollower).filter(ShopFollower.shop_id == shop_id).all()
