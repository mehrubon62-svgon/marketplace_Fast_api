from sqlalchemy.orm import Session

from models import Favorite


def get_favorites(db: Session, user_id: int):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


def add_favorite(db: Session, user_id: int, listing_id: int):
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id, Favorite.listing_id == listing_id
    ).first()
    if existing:
        return existing
    fav = Favorite(user_id=user_id, listing_id=listing_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


def remove_favorite(db: Session, user_id: int, listing_id: int):
    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id, Favorite.listing_id == listing_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return fav
