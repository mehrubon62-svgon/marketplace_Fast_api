from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user, require_admin
from modules.coupons.schemas import (
    CouponCreate,
    CouponOut,
    CouponApplyRequest,
    CouponApplyResponse,
)
from modules.coupons.crud import (
    create_coupon,
    get_coupon_by_code,
    get_all_coupons,
    deactivate_coupon,
    is_coupon_valid,
    calculate_discount,
)

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.get("/", response_model=list[CouponOut])
def list_coupons(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return get_all_coupons(db)


@router.post("/", response_model=CouponOut)
def add_coupon(
    data: CouponCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if get_coupon_by_code(db, data.code):
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    if data.discount_percent is None and data.discount_amount is None:
        raise HTTPException(
            status_code=400,
            detail="Either discount_percent or discount_amount is required",
        )
    return create_coupon(db, **data.model_dump())


@router.delete("/{coupon_id}")
def remove_coupon(coupon_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not deactivate_coupon(db, coupon_id):
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"detail": "Coupon deactivated"}


@router.post("/apply", response_model=CouponApplyResponse)
def apply_coupon(
    data: CouponApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    coupon = get_coupon_by_code(db, data.code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    valid, reason = is_coupon_valid(coupon)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    discount = calculate_discount(coupon, data.order_total)
    new_total = max(0.0, round(data.order_total - discount, 2))
    return CouponApplyResponse(
        discount=discount,
        new_total=new_total,
        coupon_id=coupon.id,
    )
