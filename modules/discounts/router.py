from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Shop, Listing, Category, DiscountScope
from modules.users.router import get_current_user
from modules.discounts.schemas import DiscountCreate, DiscountOut, PriceCheck
from modules.discounts.crud import (
    create_discount,
    get_discount_by_id,
    get_shop_discounts,
    deactivate_discount,
    get_best_discount_for_listing,
    calculate_final_price,
)

router = APIRouter(prefix="/shops/{shop_id}/discounts", tags=["Discounts"])


def _check_shop_owner(db: Session, shop_id: int, user: User) -> Shop:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not your shop")
    return shop


@router.get("/", response_model=list[DiscountOut])
def list_discounts(
    shop_id: int,
    only_active: bool = True,
    db: Session = Depends(get_db),
):
    return get_shop_discounts(db, shop_id, only_active)


@router.post("/", response_model=DiscountOut, status_code=201)
def add_discount(
    shop_id: int,
    data: DiscountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Создать скидку:
    - scope=product, target_id=listing_id — на конкретный товар
    - scope=category, target_id=category_id — на категорию
    - scope=shop, target_id=null — на все товары магазина
    """
    shop = _check_shop_owner(db, shop_id, user)

    if data.starts_at >= data.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be before ends_at")

    if data.scope == DiscountScope.shop:
        target_id = None
    else:
        if data.target_id is None:
            raise HTTPException(status_code=400, detail=f"target_id required for scope={data.scope.value}")
        if data.scope == DiscountScope.product:
            listing = db.query(Listing).filter(Listing.id == data.target_id, Listing.owner_id == shop.owner_id).first()
            if not listing:
                raise HTTPException(status_code=404, detail="Listing not found in your shop")
        elif data.scope == DiscountScope.category:
            cat = db.query(Category).filter(Category.id == data.target_id).first()
            if not cat:
                raise HTTPException(status_code=404, detail="Category not found")
        target_id = data.target_id

    return create_discount(
        db,
        shop_id=shop_id,
        scope=data.scope,
        target_id=target_id,
        discount_percent=data.discount_percent,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
    )


@router.delete("/{discount_id}")
def remove_discount(
    shop_id: int,
    discount_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_shop_owner(db, shop_id, user)
    d = get_discount_by_id(db, discount_id)
    if not d or d.shop_id != shop_id:
        raise HTTPException(status_code=404, detail="Discount not found")
    deactivate_discount(db, discount_id)
    return {"detail": "Discount deactivated"}


public_router = APIRouter(prefix="/discounts", tags=["Discounts"])


@public_router.get("/price/{listing_id}", response_model=PriceCheck)
def check_price(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    discount = get_best_discount_for_listing(db, listing)
    final_price = calculate_final_price(listing.price, discount)
    return PriceCheck(
        listing_id=listing.id,
        base_price=listing.price,
        final_price=final_price,
        discount_percent=discount.discount_percent if discount else 0.0,
        discount_id=discount.id if discount else None,
        scope=discount.scope if discount else None,
    )
