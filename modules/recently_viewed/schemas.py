from pydantic import BaseModel
from datetime import datetime


class RecentlyViewedOut(BaseModel):
    id: int
    listing_id: int
    viewed_at: datetime

    class Config:
        from_attributes = True
