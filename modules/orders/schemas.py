from pydantic import BaseModel
from datetime import datetime
from models import OrderStatus, PaymentMethodEnum


class OrderItemCreate(BaseModel):
    listing_id: int
    quantity: int = 1


class OrderCreate(BaseModel):
    address: str
    coupon_code: str | None = None
    delivery_method_id: int | None = None
    payment_method: PaymentMethodEnum | None = None  # если задан — создастся pending Payment


class OrderItemOut(BaseModel):
    id: int
    listing_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    status: OrderStatus
    total_price: float
    discount: float = 0.0
    address: str
    coupon_id: int | None = None
    delivery_method_id: int | None = None
    created_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderStatusHistoryOut(BaseModel):
    id: int
    order_id: int
    status: OrderStatus
    changed_at: datetime
    note: str | None

    class Config:
        from_attributes = True
