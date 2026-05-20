from datetime import datetime
from pydantic import BaseModel, Field
from models import TxType


class WalletOut(BaseModel):
    id: int
    user_id: int
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


class TopUpRequest(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    description: str | None = None


class WalletTransactionOut(BaseModel):
    id: int
    wallet_id: int
    amount: float
    tx_type: TxType
    description: str | None
    order_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class WalletSummary(BaseModel):
    balance: float
    total_topup: float
    total_spent: float
    total_income: float
    transactions_count: int
    transactions: list[WalletTransactionOut]


class StoreFinanceSummary(BaseModel):
    total_income: float
    period_income: float
    orders_count: int
    top_products: list[dict]
    transactions: list[WalletTransactionOut]
