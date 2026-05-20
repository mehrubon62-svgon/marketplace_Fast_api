from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Shop
from modules.users.router import get_current_user
from modules.shop_extras.schemas import (
    ShopReviewCreate,
    ShopReviewOut,
    ShopBannerCreate,
    ShopBannerOut,
    ShopFollowerOut,
)
from modules.shop_extras.crud import (
    create_shop_review,
    get_shop_reviews,
    delete_shop_review,
    create_shop_banner,
    get_shop_banners,
    delete_shop_banner,
    follow_shop,
    unfollow_shop,
    get_shop_followers,
)

router = APIRouter(tags=["Shop Extras"])


def _get_shop_or_404(db: Session, shop_id: int) -> Shop:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


# ---- Reviews ----
@router.get("/{shop_id}/reviews", response_model=list[ShopReviewOut])
def list_shop_reviews(shop_id: int, db: Session = Depends(get_db)):
    _get_shop_or_404(db, shop_id)
    return get_shop_reviews(db, shop_id)


@router.post("/{shop_id}/reviews", response_model=ShopReviewOut)
def add_shop_review(
    shop_id: int,
    data: ShopReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shop = _get_shop_or_404(db, shop_id)
    if shop.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot review your own shop")
    if not (1 <= data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    return create_shop_review(db, shop_id, user.id, data.rating, data.comment)


@router.delete("/{shop_id}/reviews/{review_id}")
def remove_shop_review(
    shop_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from models import ShopReview

    r = db.query(ShopReview).filter(ShopReview.id == review_id, ShopReview.shop_id == shop_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    if r.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    delete_shop_review(db, review_id)
    return {"detail": "Review deleted"}


# ---- Banners ----
@router.get("/{shop_id}/banners", response_model=list[ShopBannerOut])
def list_banners(shop_id: int, db: Session = Depends(get_db)):
    _get_shop_or_404(db, shop_id)
    return get_shop_banners(db, shop_id)


@router.post("/{shop_id}/banners", response_model=ShopBannerOut)
def add_banner(
    shop_id: int,
    data: ShopBannerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shop = _get_shop_or_404(db, shop_id)
    if shop.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not your shop")
    return create_shop_banner(db, shop_id, **data.model_dump())


@router.delete("/{shop_id}/banners/{banner_id}")
def remove_banner(
    shop_id: int,
    banner_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from models import ShopBanner

    b = db.query(ShopBanner).filter(ShopBanner.id == banner_id, ShopBanner.shop_id == shop_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Banner not found")
    if b.shop.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    delete_shop_banner(db, banner_id)
    return {"detail": "Banner deleted"}


# ---- Followers ----
@router.post("/{shop_id}/follow", response_model=ShopFollowerOut)
def follow(
    shop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_shop_or_404(db, shop_id)
    return follow_shop(db, shop_id, user.id)


@router.delete("/{shop_id}/follow")
def unfollow(
    shop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not unfollow_shop(db, shop_id, user.id):
        raise HTTPException(status_code=404, detail="Not following this shop")
    return {"detail": "Unfollowed"}


@router.get("/{shop_id}/followers", response_model=list[ShopFollowerOut])
def list_followers(shop_id: int, db: Session = Depends(get_db)):
    _get_shop_or_404(db, shop_id)
    return get_shop_followers(db, shop_id)
