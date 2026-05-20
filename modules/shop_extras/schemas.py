from pydantic import BaseModel
from datetime import datetime


class ShopReviewCreate(BaseModel):
    rating: int
    comment: str | None = None


class ShopReviewOut(BaseModel):
    id: int
    shop_id: int
    author_id: int
    rating: int
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ShopBannerCreate(BaseModel):
    image_url: str
    title: str | None = None
    is_active: bool = True


class ShopBannerOut(BaseModel):
    id: int
    shop_id: int
    image_url: str
    title: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ShopFollowerOut(BaseModel):
    id: int
    shop_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
