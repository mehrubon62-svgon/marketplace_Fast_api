from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Wallet, WalletTransaction, TxType, Order, OrderItem, Listing


def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    """Получить или создать кошелёк (на случай старых пользователей до интеграции)."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet:
        return wallet
    wallet = Wallet(user_id=user_id, balance=0.0)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def get_wallet_by_user(db: Session, user_id: int) -> Wallet | None:
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()


def add_transaction(
    db: Session,
    wallet: Wallet,
    amount: float,
    tx_type: TxType,
    description: str | None = None,
    order_id: int | None = None,
    commit: bool = True,
) -> WalletTransaction:
    """Создаёт транзакцию и обновляет баланс. По умолчанию коммитит."""
    wallet.balance += amount
    tx = WalletTransaction(
        wallet_id=wallet.id,
        amount=amount,
        tx_type=tx_type,
        description=description,
        order_id=order_id,
    )
    db.add(tx)
    if commit:
        db.commit()
        db.refresh(tx)
    return tx


def get_transactions(
    db: Session,
    wallet_id: int,
    tx_type: TxType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    q = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet_id)
    if tx_type:
        q = q.filter(WalletTransaction.tx_type == tx_type)
    if date_from:
        q = q.filter(WalletTransaction.created_at >= date_from)
    if date_to:
        q = q.filter(WalletTransaction.created_at <= date_to)
    return q.order_by(WalletTransaction.created_at.desc()).all()


def get_summary(db: Session, wallet_id: int) -> dict:
    txs = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet_id).all()
    total_topup = sum(t.amount for t in txs if t.tx_type == TxType.topup)
    total_spent = sum(abs(t.amount) for t in txs if t.tx_type == TxType.order_payment)
    total_income = sum(t.amount for t in txs if t.tx_type in (TxType.order_income, TxType.refund))
    return {
        "total_topup": total_topup,
        "total_spent": total_spent,
        "total_income": total_income,
        "transactions_count": len(txs),
    }


def get_store_finance(
    db: Session,
    seller_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    """Финансовый отчёт для магазина."""
    wallet = get_wallet_by_user(db, seller_id)
    if not wallet:
        return {
            "total_income": 0.0,
            "period_income": 0.0,
            "orders_count": 0,
            "top_products": [],
            "transactions": [],
        }

    # Все доходные транзакции
    all_q = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id,
        WalletTransaction.tx_type == TxType.order_income,
    )
    all_txs = all_q.order_by(WalletTransaction.created_at.desc()).all()
    total_income = sum(t.amount for t in all_txs)

    # За период
    period_q = all_q
    if date_from:
        period_q = period_q.filter(WalletTransaction.created_at >= date_from)
    if date_to:
        period_q = period_q.filter(WalletTransaction.created_at <= date_to)
    period_txs = period_q.all()
    period_income = sum(t.amount for t in period_txs)

    # Топ товаров по выручке (среди заказов магазина)
    top_q = (
        db.query(
            OrderItem.listing_id,
            Listing.title,
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            func.sum(OrderItem.quantity).label("qty"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Listing, OrderItem.listing_id == Listing.id)
        .filter(Order.seller_id == seller_id)
        .group_by(OrderItem.listing_id, Listing.title)
        .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
        .limit(5)
    )
    top_products = [
        {"listing_id": r.listing_id, "title": r.title, "revenue": float(r.revenue), "quantity": int(r.qty)}
        for r in top_q.all()
    ]

    # Кол-во заказов магазина
    orders_count = db.query(Order).filter(Order.seller_id == seller_id).count()

    return {
        "total_income": total_income,
        "period_income": period_income,
        "orders_count": orders_count,
        "top_products": top_products,
        "transactions": all_txs[:50],
    }
