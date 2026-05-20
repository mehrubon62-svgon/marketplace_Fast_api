from sqlalchemy.orm import Session

from models import Review


def create_review(
    db: Session,
    rating: int,
    comment: str | None,
    listing_id: int,
    author_id: int,
    order_id: int | None = None,
):
    review = Review(
        rating=rating,
        comment=comment,
        listing_id=listing_id,
        author_id=author_id,
        order_id=order_id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews_by_listing(db: Session, listing_id: int):
    return db.query(Review).filter(Review.listing_id == listing_id).order_by(Review.created_at.desc()).all()


def get_review_by_id(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()


def delete_review(db: Session, review_id: int):
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        db.delete(review)
        db.commit()
    return review


def user_already_reviewed_for_order(db: Session, listing_id: int, author_id: int, order_id: int) -> bool:
    return db.query(Review).filter(
        Review.listing_id == listing_id,
        Review.author_id == author_id,
        Review.order_id == order_id,
    ).first() is not None


def user_already_reviewed(db: Session, listing_id: int, author_id: int) -> bool:
    return db.query(Review).filter(
        Review.listing_id == listing_id, Review.author_id == author_id
    ).first() is not None
