from pydantic import BaseModel


class FavoriteAdd(BaseModel):
    listing_id: int


class FavoriteOut(BaseModel):
    id: int
    listing_id: int

    class Config:
        from_attributes = True
