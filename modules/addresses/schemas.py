from pydantic import BaseModel


class AddressCreate(BaseModel):
    full_name: str
    phone: str
    country: str
    city: str
    street: str
    postal_code: str | None = None
    is_default: bool = False


class AddressUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    street: str | None = None
    postal_code: str | None = None
    is_default: bool | None = None


class AddressOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str
    country: str
    city: str
    street: str
    postal_code: str | None
    is_default: bool

    class Config:
        from_attributes = True
