from pydantic import BaseModel, Field
from datetime import datetime


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    listing_id: int
    order_id: int | None = None


class ReviewOut(BaseModel):
    id: int
    rating: int
    comment: str | None
    listing_id: int
    author_id: int
    order_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
