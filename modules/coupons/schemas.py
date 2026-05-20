from pydantic import BaseModel
from datetime import datetime


class CouponCreate(BaseModel):
    code: str
    discount_percent: float | None = None
    discount_amount: float | None = None
    max_uses: int | None = None
    expires_at: datetime | None = None


class CouponOut(BaseModel):
    id: int
    code: str
    discount_percent: float | None
    discount_amount: float | None
    max_uses: int | None
    times_used: int
    expires_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class CouponApplyRequest(BaseModel):
    code: str
    order_total: float


class CouponApplyResponse(BaseModel):
    discount: float
    new_total: float
    coupon_id: int
