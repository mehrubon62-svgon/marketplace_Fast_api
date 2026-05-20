from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, TxType, NotificationType
from modules.users.router import get_current_user, require_admin
from modules.notifications.crud import create_notification
from modules.wallet.schemas import (
    WalletOut,
    TopUpRequest,
    WalletTransactionOut,
    WalletSummary,
    StoreFinanceSummary,
)
from modules.wallet.crud import (
    get_or_create_wallet,
    get_wallet_by_user,
    add_transaction,
    get_transactions,
    get_summary,
    get_store_finance,
)
from modules.websockets.manager import manager

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/me", response_model=WalletOut)
def my_wallet(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_or_create_wallet(db, user.id)


@router.post("/topup", response_model=WalletOut)
async def admin_topup(
    data: TopUpRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Только администратор может пополнять баланс любому пользователю."""
    target = db.query(User).filter(User.id == data.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = get_or_create_wallet(db, data.user_id)
    description = data.description or f"Пополнение администратором ({admin.username})"
    add_transaction(db, wallet, data.amount, TxType.topup, description)

    create_notification(
        db,
        user_id=data.user_id,
        title="Баланс пополнен",
        body=f"+{data.amount:.2f}. Новый баланс: {wallet.balance:.2f}",
        type=NotificationType.wallet,
    )

    await manager.send_personal(data.user_id, {
        "event": "wallet_topup",
        "amount": data.amount,
        "new_balance": wallet.balance,
        "by": admin.username,
    })

    db.refresh(wallet)
    return wallet


@router.get("/transactions", response_model=list[WalletTransactionOut])
def my_transactions(
    tx_type: TxType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """История транзакций текущего пользователя с фильтрацией по типу/периоду."""
    wallet = get_or_create_wallet(db, user.id)
    return get_transactions(db, wallet.id, tx_type, date_from, date_to)


@router.get("/summary", response_model=WalletSummary)
def my_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Сводка по своему балансу."""
    wallet = get_or_create_wallet(db, user.id)
    summary = get_summary(db, wallet.id)
    txs = get_transactions(db, wallet.id)
    return WalletSummary(
        balance=wallet.balance,
        total_topup=summary["total_topup"],
        total_spent=summary["total_spent"],
        total_income=summary["total_income"],
        transactions_count=summary["transactions_count"],
        transactions=txs[:50],
    )


@router.get("/store/{shop_id}/finance", response_model=StoreFinanceSummary)
def store_finance(
    shop_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Финансовый отчёт магазина (только для владельца или админа)."""
    from models import Shop
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not your shop")

    return get_store_finance(db, shop.owner_id, date_from, date_to)
