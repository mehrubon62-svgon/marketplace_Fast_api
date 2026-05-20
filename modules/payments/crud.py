import secrets
from sqlalchemy.orm import Session
from models import Payment, Refund, PaymentStatus, Order


def create_payment(
    db: Session,
    order: Order,
    method,
) -> Payment:
    """Создаёт платёж в pending. Имитирует обращение к платёжному шлюзу."""
    payment = Payment(
        order_id=order.id,
        amount=order.total_price,
        method=method,
        status=PaymentStatus.pending,
        transaction_id=f"tx_{secrets.token_hex(8)}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_payment(db: Session, payment_id: int) -> Payment | None:
    """Подтвердить успешный платёж (имитация)."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        return None
    payment.status = PaymentStatus.paid
    db.commit()
    db.refresh(payment)
    return payment


def fail_payment(db: Session, payment_id: int) -> Payment | None:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        return None
    payment.status = PaymentStatus.failed
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payment_by_order(db: Session, order_id: int):
    return db.query(Payment).filter(Payment.order_id == order_id).first()


def create_refund(db: Session, payment: Payment, amount: float | None, reason: str | None) -> Refund:
    refund_amount = amount if amount is not None else payment.amount
    refund = Refund(payment_id=payment.id, amount=refund_amount, reason=reason)
    db.add(refund)
    payment.status = PaymentStatus.refunded
    db.commit()
    db.refresh(refund)
    return refund
