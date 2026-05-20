from sqlalchemy.orm import Session

from models import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    CartItem,
    Coupon,
    DeliveryMethod,
)


def _record_status(db: Session, order_id: int, status: OrderStatus, note: str | None = None):
    history = OrderStatusHistory(order_id=order_id, status=status, note=note)
    db.add(history)


def create_order_from_cart(
    db: Session,
    buyer_id: int,
    seller_id: int,
    address: str,
    items: list[CartItem],
    coupon: Coupon | None = None,
    delivery_method: DeliveryMethod | None = None,
    item_prices: dict | None = None,
):
    subtotal = 0.0
    order = Order(
        buyer_id=buyer_id,
        seller_id=seller_id,
        address=address,
        total_price=0,
        coupon_id=coupon.id if coupon else None,
        delivery_method_id=delivery_method.id if delivery_method else None,
    )
    db.add(order)
    db.flush()

    for cart_item in items:
        listing = cart_item.listing
        unit_price = item_prices.get(cart_item.id, listing.price) if item_prices else listing.price
        item_price = unit_price * cart_item.quantity
        subtotal += item_price

        order_item = OrderItem(
            order_id=order.id,
            listing_id=cart_item.listing_id,
            quantity=cart_item.quantity,
            price=unit_price,
        )
        db.add(order_item)

        listing.quantity -= cart_item.quantity
        if listing.quantity <= 0:
            listing.is_active = False

    discount = 0.0
    if coupon:
        if coupon.discount_percent:
            discount = round(subtotal * coupon.discount_percent / 100.0, 2)
        elif coupon.discount_amount:
            discount = min(coupon.discount_amount, subtotal)

    delivery_cost = delivery_method.price if delivery_method else 0.0
    total = max(0.0, round(subtotal - discount + delivery_cost, 2))

    order.discount = discount
    order.total_price = total

    _record_status(db, order.id, OrderStatus.pending, "Order created")
    db.commit()
    db.refresh(order)
    return order


def get_orders_by_buyer(db: Session, buyer_id: int):
    return db.query(Order).filter(Order.buyer_id == buyer_id).order_by(Order.created_at.desc()).all()


def get_orders_by_seller(db: Session, seller_id: int):
    return db.query(Order).filter(Order.seller_id == seller_id).order_by(Order.created_at.desc()).all()


def get_order_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def update_order_status(db: Session, order_id: int, status: OrderStatus, note: str | None = None):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        _record_status(db, order_id, status, note)
        db.commit()
        db.refresh(order)
    return order


def get_order_history(db: Session, order_id: int):
    return (
        db.query(OrderStatusHistory)
        .filter(OrderStatusHistory.order_id == order_id)
        .order_by(OrderStatusHistory.changed_at)
        .all()
    )


def get_all_orders(db: Session):
    return db.query(Order).order_by(Order.created_at.desc()).all()
