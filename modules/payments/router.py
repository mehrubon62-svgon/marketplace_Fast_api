from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Order, PaymentStatus, NotificationType
from modules.users.router import get_current_user, require_admin
from modules.payments.schemas import (
    PaymentCreate,
    PaymentOut,
    RefundCreate,
    RefundOut,
)
from modules.payments.crud import (
    create_payment,
    confirm_payment,
    fail_payment,
    get_payment,
    get_payment_by_order,
    create_refund,
)
from modules.notifications.crud import create_notification

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentOut)
def initiate_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if order.payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this order")

    return create_payment(db, order, data.method)


@router.post("/{payment_id}/confirm", response_model=PaymentOut)
def confirm(payment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Имитация колбэка от платёжного шлюза."""
    payment = get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.order.buyer_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    if payment.status != PaymentStatus.pending:
        raise HTTPException(status_code=400, detail="Payment is not in pending state")
    confirmed = confirm_payment(db, payment_id)

    # уведомления обеим сторонам
    create_notification(
        db,
        user_id=confirmed.order.seller_id,
        title=f"Оплачен заказ #{confirmed.order.id}",
        body=f"Сумма: {confirmed.amount}",
        type=NotificationType.order,
    )
    create_notification(
        db,
        user_id=confirmed.order.buyer_id,
        title="Платёж прошёл",
        body=f"Заказ #{confirmed.order.id} оплачен",
        type=NotificationType.order,
    )
    return confirmed


@router.post("/{payment_id}/fail", response_model=PaymentOut)
def fail(payment_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    payment = get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return fail_payment(db, payment_id)


@router.get("/order/{order_id}", response_model=PaymentOut)
def get_by_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payment = get_payment_by_order(db, order_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.order.buyer_id != user.id and payment.order.seller_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return payment


@router.post("/refund", response_model=RefundOut)
def refund(
    data: RefundCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    payment = get_payment(db, data.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.order.seller_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only seller or admin can issue refund")
    if payment.status != PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Only paid payments can be refunded")
    return create_refund(db, payment, data.amount, data.reason)
