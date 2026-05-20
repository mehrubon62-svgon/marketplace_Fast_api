from pydantic import BaseModel, Field
from datetime import datetime


class BannerCreate(BaseModel):
    image_url: str
    title: str | None = None
    link: str | None = None
    is_active: bool = True
    sort_order: int = 0


class BannerOut(BaseModel):
    id: int
    image_url: str
    title: str | None
    link: str | None
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


class FlashSaleListingShort(BaseModel):
    id: int
    title: str
    price: float
    image_url: str | None = None

    class Config:
        from_attributes = True


class FlashSaleCreate(BaseModel):
    listing_ids: list[int] = Field(..., min_length=1, description="Один или несколько id товаров")
    discount_percent: float = Field(..., gt=0, le=100)
    title: str | None = None
    starts_at: datetime
    ends_at: datetime


class FlashSaleUpdate(BaseModel):
    title: str | None = None
    discount_percent: float | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


class FlashSaleListingsUpdate(BaseModel):
    listing_ids: list[int] = Field(..., min_length=1)


class FlashSaleOut(BaseModel):
    id: int
    title: str | None = None
    discount_percent: float
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    listings: list[FlashSaleListingShort] = []

    class Config:
        from_attributes = True
