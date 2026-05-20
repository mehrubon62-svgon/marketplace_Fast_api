from pydantic import BaseModel


class ListingCreate(BaseModel):
    title: str
    description: str | None = None
    price: float
    image_url: str | None = None
    category_id: int
    brand_id: int | None = None


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    image_url: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    quantity: int | None = None
    is_active: bool | None = None


class TagShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BrandShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ListingOut(BaseModel):
    id: int
    title: str
    description: str | None
    price: float
    quantity: int
    image_url: str | None
    is_active: bool
    category_id: int
    owner_id: int
    brand_id: int | None = None
    brand: BrandShort | None = None
    tags: list[TagShort] = []

    class Config:
        from_attributes = True
