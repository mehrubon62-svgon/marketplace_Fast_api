from datetime import datetime
from pydantic import BaseModel
from models import ShopStatus


class ShopCreate(BaseModel):
    name: str
    description: str | None = None


class ShopOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: ShopStatus
    owner_id: int

    class Config:
        from_attributes = True


class ShopStatusUpdate(BaseModel):
    status: ShopStatus


class ShopOwnerShort(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class ShopListingShort(BaseModel):
    id: int
    title: str
    price: float
    image_url: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ShopDetailOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: ShopStatus
    owner: ShopOwnerShort
    created_at: datetime
    rating_avg: float | None
    reviews_count: int
    followers_count: int
    listings_count: int
    listings: list[ShopListingShort]
