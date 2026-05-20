from sqlalchemy.orm import Session
from models import Review, ReviewReply, ReviewImage, ReviewVote


def add_reply(db: Session, review_id: int, author_id: int, text: str) -> ReviewReply:
    reply = ReviewReply(review_id=review_id, author_id=author_id, text=text)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def get_reply(db: Session, review_id: int):
    return db.query(ReviewReply).filter(ReviewReply.review_id == review_id).first()


def add_image(db: Session, review_id: int, url: str) -> ReviewImage:
    img = ReviewImage(review_id=review_id, url=url)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def get_images(db: Session, review_id: int):
    return db.query(ReviewImage).filter(ReviewImage.review_id == review_id).all()


def vote_review(db: Session, review_id: int, user_id: int, is_helpful: bool) -> ReviewVote:
    existing = (
        db.query(ReviewVote)
        .filter(ReviewVote.review_id == review_id, ReviewVote.user_id == user_id)
        .first()
    )
    if existing:
        existing.is_helpful = is_helpful
        db.commit()
        db.refresh(existing)
        return existing
    v = ReviewVote(review_id=review_id, user_id=user_id, is_helpful=is_helpful)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def get_votes_summary(db: Session, review_id: int) -> dict:
    helpful = db.query(ReviewVote).filter(ReviewVote.review_id == review_id, ReviewVote.is_helpful == True).count()
    not_helpful = db.query(ReviewVote).filter(ReviewVote.review_id == review_id, ReviewVote.is_helpful == False).count()
    return {"helpful": helpful, "not_helpful": not_helpful}
