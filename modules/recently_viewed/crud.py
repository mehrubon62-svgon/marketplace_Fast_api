from datetime import datetime
from sqlalchemy.orm import Session
from models import RecentlyViewed

LIMIT = 30


def track_view(db: Session, user_id: int, listing_id: int) -> RecentlyViewed:
    existing = (
        db.query(RecentlyViewed)
        .filter(RecentlyViewed.user_id == user_id, RecentlyViewed.listing_id == listing_id)
        .first()
    )
    if existing:
        existing.viewed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    rv = RecentlyViewed(user_id=user_id, listing_id=listing_id)
    db.add(rv)
    db.commit()
    db.refresh(rv)

    extras = (
        db.query(RecentlyViewed)
        .filter(RecentlyViewed.user_id == user_id)
        .order_by(RecentlyViewed.viewed_at.desc())
        .offset(LIMIT)
        .all()
    )
    for e in extras:
        db.delete(e)
    if extras:
        db.commit()
    return rv


def get_recent(db: Session, user_id: int, limit: int = 10):
    return (
        db.query(RecentlyViewed)
        .filter(RecentlyViewed.user_id == user_id)
        .order_by(RecentlyViewed.viewed_at.desc())
        .limit(limit)
        .all()
    )
