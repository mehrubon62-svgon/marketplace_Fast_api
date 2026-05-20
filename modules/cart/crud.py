from sqlalchemy.orm import Session

from models import CartItem


def get_cart_items(db: Session, user_id: int):
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


def add_to_cart(db: Session, user_id: int, listing_id: int, quantity: int = 1):
    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id, CartItem.listing_id == listing_id
    ).first()
    if existing:
        existing.quantity += quantity
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(user_id=user_id, listing_id=listing_id, quantity=quantity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item_quantity(db: Session, item_id: int, user_id: int, quantity: int):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if item:
        if quantity <= 0:
            db.delete(item)
            db.commit()
            return None
        item.quantity = quantity
        db.commit()
        db.refresh(item)
    return item


def remove_from_cart(db: Session, item_id: int, user_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if item:
        db.delete(item)
        db.commit()
    return item


def clear_cart(db: Session, user_id: int):
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
