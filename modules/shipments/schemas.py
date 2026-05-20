from pydantic import BaseModel
from datetime import datetime


class ShipmentCreate(BaseModel):
    order_id: int
    tracking_number: str | None = None
    carrier: str | None = None


class ShipmentUpdate(BaseModel):
    tracking_number: str | None = None
    carrier: str | None = None
    status: str | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None


class ShipmentOut(BaseModel):
    id: int
    order_id: int
    tracking_number: str | None
    carrier: str | None
    status: str
    shipped_at: datetime | None
    delivered_at: datetime | None

    class Config:
        from_attributes = True


class DeliveryMethodCreate(BaseModel):
    name: str
    price: float = 0.0
    estimated_days: int = 3
    is_active: bool = True


class DeliveryMethodOut(BaseModel):
    id: int
    name: str
    price: float
    estimated_days: int
    is_active: bool

    class Config:
        from_attributes = True
