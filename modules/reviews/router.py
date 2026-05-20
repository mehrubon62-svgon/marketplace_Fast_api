from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Order, OrderStatus, OrderItem
from modules.users.router import get_current_user
from modules.reviews.schemas import ReviewCreate, ReviewOut
from modules.reviews.crud import (
    create_review,
    get_reviews_by_listing,
    get_review_by_id,
    delete_review,
    user_already_reviewed_for_order,
)
from modules.listings.crud import get_listing_by_id

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewOut)
def add_review(data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Оставить отзыв на товар.
    Требуется передать order_id заказа со статусом 'delivered', содержащего этот товар.
    """
    listing = get_listing_by_id(db, data.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review your own listing")

    if data.order_id is None:
        raise HTTPException(status_code=400, detail="order_id required (review only after delivery)")

    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if order.status != OrderStatus.delivered:
        raise HTTPException(status_code=400, detail="Can only review after order is delivered")

    # Проверка что товар был в этом заказе
    has_item = db.query(OrderItem).filter(
        OrderItem.order_id == order.id, OrderItem.listing_id == data.listing_id
    ).first()
    if not has_item:
        raise HTTPException(status_code=400, detail="This listing is not in the order")

    if user_already_reviewed_for_order(db, data.listing_id, current_user.id, data.order_id):
        raise HTTPException(status_code=400, detail="Already reviewed this product for this order")

    return create_review(db, data.rating, data.comment, data.listing_id, current_user.id, data.order_id)


@router.get("/listing/{listing_id}", response_model=list[ReviewOut])
def list_reviews(listing_id: int, db: Session = Depends(get_db)):
    return get_reviews_by_listing(db, listing_id)


@router.delete("/{review_id}")
def remove_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    delete_review(db, review_id)
    return {"detail": "Review deleted"}
