from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Review
from modules.users.router import get_current_user
from modules.review_extras.schemas import (
    ReviewReplyCreate,
    ReviewReplyOut,
    ReviewImageCreate,
    ReviewImageOut,
    ReviewVoteRequest,
    ReviewVoteOut,
)
from modules.review_extras.crud import (
    add_reply,
    get_reply,
    add_image,
    get_images,
    vote_review,
    get_votes_summary,
)

router = APIRouter(tags=["Review Extras"])


def _get_review(db: Session, review_id: int) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/{review_id}/reply", response_model=ReviewReplyOut)
def reply_to_review(
    review_id: int,
    data: ReviewReplyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = _get_review(db, review_id)
    if review.listing.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only seller can reply to reviews on their listing")
    if get_reply(db, review_id):
        raise HTTPException(status_code=400, detail="Reply already exists")
    return add_reply(db, review_id, user.id, data.text)


@router.get("/{review_id}/reply", response_model=ReviewReplyOut)
def fetch_reply(review_id: int, db: Session = Depends(get_db)):
    _get_review(db, review_id)
    reply = get_reply(db, review_id)
    if not reply:
        raise HTTPException(status_code=404, detail="No reply yet")
    return reply


@router.post("/{review_id}/images", response_model=ReviewImageOut)
def upload_review_image(
    review_id: int,
    data: ReviewImageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = _get_review(db, review_id)
    if review.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your review")
    return add_image(db, review_id, data.url)


@router.get("/{review_id}/images", response_model=list[ReviewImageOut])
def list_review_images(review_id: int, db: Session = Depends(get_db)):
    _get_review(db, review_id)
    return get_images(db, review_id)


@router.post("/{review_id}/vote", response_model=ReviewVoteOut)
def vote(
    review_id: int,
    data: ReviewVoteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = _get_review(db, review_id)
    if review.author_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own review")
    return vote_review(db, review_id, user.id, data.is_helpful)


@router.get("/{review_id}/votes")
def votes_summary(review_id: int, db: Session = Depends(get_db)):
    _get_review(db, review_id)
    return get_votes_summary(db, review_id)
