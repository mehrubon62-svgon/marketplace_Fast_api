from pydantic import BaseModel


class CartItemAdd(BaseModel):
    listing_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    listing_id: int
    quantity: int

    class Config:
        from_attributes = True
