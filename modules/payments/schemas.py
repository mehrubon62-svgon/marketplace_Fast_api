from pydantic import BaseModel
from datetime import datetime
from models import PaymentMethodEnum, PaymentStatus


class PaymentCreate(BaseModel):
    order_id: int
    method: PaymentMethodEnum


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    method: PaymentMethodEnum
    status: PaymentStatus
    transaction_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RefundCreate(BaseModel):
    payment_id: int
    amount: float | None = None  # если None — полный возврат
    reason: str | None = None


class RefundOut(BaseModel):
    id: int
    payment_id: int
    amount: float
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True
