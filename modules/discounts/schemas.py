from datetime import datetime
from pydantic import BaseModel, Field
from models import DiscountScope


class DiscountCreate(BaseModel):
    scope: DiscountScope
    target_id: int | None = None
    discount_percent: float = Field(..., gt=0, le=100)
    starts_at: datetime
    ends_at: datetime


class DiscountOut(BaseModel):
    id: int
    shop_id: int
    scope: DiscountScope
    target_id: int | None
    discount_percent: float
    starts_at: datetime
    ends_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PriceCheck(BaseModel):
    listing_id: int
    base_price: float
    final_price: float
    discount_percent: float
    discount_id: int | None = None
    scope: DiscountScope | None = None
