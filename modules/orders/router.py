from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import (
    get_db,
    User,
    OrderStatus,
    ShopStatus,
    DeliveryMethod,
    NotificationType,
    TxType,
)
from modules.users.router import get_current_user, require_admin
from modules.orders.schemas import (
    OrderCreate,
    OrderOut,
    OrderStatusUpdate,
    OrderStatusHistoryOut,
)
from modules.orders.crud import (
    create_order_from_cart,
    get_orders_by_buyer,
    get_orders_by_seller,
    get_order_by_id,
    update_order_status,
    get_all_orders,
    get_order_history,
)
from modules.cart.crud import get_cart_items, clear_cart
from modules.coupons.crud import (
    get_coupon_by_code,
    is_coupon_valid,
    register_usage,
)
from modules.payments.crud import create_payment
from modules.notifications.crud import create_notification
from modules.wallet.crud import get_or_create_wallet, add_transaction
from modules.discounts.crud import get_best_discount_for_listing, calculate_final_price
from modules.websockets.manager import manager

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/checkout", response_model=list[OrderOut])
async def checkout(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Оформление заказа:
    1) Применяются скидки магазина (product/category/shop scope) к товарам.
    2) Сумма списывается с баланса покупателя.
    3) Каждому магазину зачисляется его доход.
    4) Магазины получают realtime-уведомление.
    Все финансовые операции атомарны.
    """
    cart_items = get_cart_items(db, current_user.id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    for item in cart_items:
        if not item.listing.is_active:
            raise HTTPException(status_code=400, detail=f"Listing '{item.listing.title}' is no longer available")
        if item.quantity > item.listing.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for '{item.listing.title}'")

    item_prices = {}
    for item in cart_items:
        discount = get_best_discount_for_listing(db, item.listing)
        effective = calculate_final_price(item.listing.price, discount)
        item_prices[item.id] = effective

    coupon = None
    if data.coupon_code:
        coupon = get_coupon_by_code(db, data.coupon_code)
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        valid, reason = is_coupon_valid(coupon)
        if not valid:
            raise HTTPException(status_code=400, detail=reason)

    delivery_method = None
    if data.delivery_method_id:
        delivery_method = (
            db.query(DeliveryMethod)
            .filter(DeliveryMethod.id == data.delivery_method_id, DeliveryMethod.is_active == True)
            .first()
        )
        if not delivery_method:
            raise HTTPException(status_code=404, detail="Delivery method not found")

    sellers: dict[int, list] = {}
    for item in cart_items:
        sellers.setdefault(item.listing.owner_id, []).append(item)

    grand_total = 0.0
    seller_totals = {}
    for seller_id, items in sellers.items():
        subtotal = sum(item_prices[i.id] * i.quantity for i in items)
        discount_coupon = 0.0
        if coupon:
            if coupon.discount_percent:
                discount_coupon = round(subtotal * coupon.discount_percent / 100.0, 2)
            elif coupon.discount_amount:
                discount_coupon = min(coupon.discount_amount, subtotal)
        delivery_cost = delivery_method.price if delivery_method else 0.0
        total = max(0.0, round(subtotal - discount_coupon + delivery_cost, 2))
        seller_totals[seller_id] = total
        grand_total += total

    buyer_wallet = get_or_create_wallet(db, current_user.id)
    if buyer_wallet.balance < grand_total:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Need {grand_total:.2f}, have {buyer_wallet.balance:.2f}",
        )

    orders = []
    for seller_id, items in sellers.items():
        order = create_order_from_cart(
            db, current_user.id, seller_id, data.address, items, coupon, delivery_method,
            item_prices=item_prices,
        )

        if data.payment_method:
            create_payment(db, order, data.payment_method)

        orders.append(order)

    try:
        add_transaction(
            db,
            buyer_wallet,
            -grand_total,
            TxType.order_payment,
            description=f"Оплата заказов ({len(orders)} шт.)",
            order_id=orders[0].id if orders else None,
            commit=False,
        )
        for seller_id, total in seller_totals.items():
            seller_wallet = get_or_create_wallet(db, seller_id)
            order_for_seller = next(o for o in orders if o.seller_id == seller_id)
            add_transaction(
                db,
                seller_wallet,
                total,
                TxType.order_income,
                description=f"Доход от заказа #{order_for_seller.id}",
                order_id=order_for_seller.id,
                commit=False,
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    for order in orders:
        create_notification(
            db,
            user_id=order.seller_id,
            title="Новый заказ",
            body=f"Заказ #{order.id} на сумму {order.total_price:.2f}",
            type=NotificationType.order,
        )
        await manager.send_personal(order.seller_id, {
            "event": "new_order",
            "order_id": order.id,
            "total": order.total_price,
            "buyer_id": current_user.id,
            "status": "pending",
            "items": [
                {"listing_id": it.listing_id, "quantity": it.quantity, "price": it.price}
                for it in order.items
            ],
        })

    if coupon and orders:
        register_usage(db, coupon, current_user.id, orders[0].id)

    create_notification(
        db,
        user_id=current_user.id,
        title="Заказ оформлен",
        body=f"Создано заказов: {len(orders)}. Списано: {grand_total:.2f}",
        type=NotificationType.order,
    )
    await manager.send_personal(current_user.id, {
        "event": "checkout_done",
        "orders_count": len(orders),
        "total_charged": grand_total,
        "new_balance": buyer_wallet.balance,
    })

    clear_cart(db, current_user.id)
    return orders


@router.get("/my", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_orders_by_buyer(db, current_user.id)


@router.get("/sales", response_model=list[OrderOut])
def my_sales(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.shop or current_user.shop.status != ShopStatus.approved:
        raise HTTPException(status_code=403, detail="You don't have an approved shop")
    return get_orders_by_seller(db, current_user.id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
async def change_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.id == order.buyer_id:
        if data.status != OrderStatus.cancelled:
            raise HTTPException(status_code=403, detail="Buyer can only cancel orders")
        if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
            raise HTTPException(status_code=400, detail="Cannot cancel order in this status")
    elif current_user.id == order.seller_id:
        pass
    elif current_user.role.value == "admin":
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = update_order_status(db, order_id, data.status, data.note)

    if data.status == OrderStatus.cancelled and order.total_price > 0:
        try:
            buyer_wallet = get_or_create_wallet(db, order.buyer_id)
            seller_wallet = get_or_create_wallet(db, order.seller_id)
            add_transaction(
                db, buyer_wallet, order.total_price, TxType.refund,
                description=f"Возврат за заказ #{order.id}", order_id=order.id, commit=False,
            )
            add_transaction(
                db, seller_wallet, -order.total_price, TxType.refund,
                description=f"Списание (отмена заказа #{order.id})", order_id=order.id, commit=False,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    notify_user_id = order.buyer_id if current_user.id != order.buyer_id else order.seller_id
    create_notification(
        db,
        user_id=notify_user_id,
        title=f"Заказ #{order.id}: {data.status.value}",
        body=data.note,
        type=NotificationType.order,
    )
    await manager.send_personal(notify_user_id, {
        "event": "order_status_changed",
        "order_id": order.id,
        "new_status": data.status.value,
        "note": data.note,
    })

    return updated


@router.get("/{order_id}/history", response_model=list[OrderStatusHistoryOut])
def order_history(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return get_order_history(db, order_id)


@router.get("/", response_model=list[OrderOut])
def all_orders(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return get_all_orders(db)
