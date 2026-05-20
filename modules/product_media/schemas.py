from pydantic import BaseModel


class ProductImageCreate(BaseModel):
    url: str
    is_primary: bool = False
    sort_order: int = 0


class ProductImageOut(BaseModel):
    id: int
    listing_id: int
    url: str
    is_primary: bool
    sort_order: int

    class Config:
        from_attributes = True


class ProductVariantCreate(BaseModel):
    name: str
    price: float
    quantity: int = 0
    sku: str | None = None


class ProductVariantOut(BaseModel):
    id: int
    listing_id: int
    name: str
    price: float
    quantity: int
    sku: str | None

    class Config:
        from_attributes = True
