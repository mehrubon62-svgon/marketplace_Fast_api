from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, ShopStatus
from modules.users.router import get_current_user, require_admin
from modules.shops.schemas import (
    ShopCreate,
    ShopOut,
    ShopStatusUpdate,
    ShopDetailOut,
    ShopOwnerShort,
    ShopListingShort,
)
from modules.shops.crud import (
    create_shop,
    get_shop_by_owner,
    get_shop_by_id,
    get_all_shops,
    get_pending_shops,
    update_shop_status,
    get_shop_detail,
)

router = APIRouter(prefix="/shops", tags=["Shops"])


@router.post("/apply", response_model=ShopOut)
def apply_for_shop(data: ShopCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = get_shop_by_owner(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="You already have a shop application")
    shop = create_shop(db, data.name, data.description, current_user.id)
    return shop


@router.get("/my", response_model=ShopOut | None)
def get_my_shop(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_shop_by_owner(db, current_user.id)


@router.get("/", response_model=list[ShopOut])
def list_all_shops(db: Session = Depends(get_db)):
    shops = get_all_shops(db)
    return [s for s in shops if s.status == ShopStatus.approved]


@router.get("/pending", response_model=list[ShopOut])
def list_pending_shops(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return get_pending_shops(db)


@router.get("/{shop_id}", response_model=ShopDetailOut)
def shop_detail(shop_id: int, db: Session = Depends(get_db)):
    """
    Подробная информация о магазине: владелец, рейтинг, количество отзывов,
    подписчиков и список активных товаров.
    """
    detail = get_shop_detail(db, shop_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Shop not found")

    shop = detail["shop"]
    return ShopDetailOut(
        id=shop.id,
        name=shop.name,
        description=shop.description,
        status=shop.status,
        owner=ShopOwnerShort.model_validate(shop.owner),
        created_at=shop.created_at,
        rating_avg=detail["rating_avg"],
        reviews_count=detail["reviews_count"],
        followers_count=detail["followers_count"],
        listings_count=len(detail["listings"]),
        listings=[ShopListingShort.model_validate(l) for l in detail["listings"]],
    )


@router.patch("/{shop_id}/status", response_model=ShopOut)
def change_shop_status(
    shop_id: int,
    data: ShopStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    shop = update_shop_status(db, shop_id, data.status)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop
