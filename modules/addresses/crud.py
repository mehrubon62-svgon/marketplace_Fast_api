from sqlalchemy.orm import Session

from models import Address


def create_address(db: Session, user_id: int, **kwargs) -> Address:
    if kwargs.get("is_default"):
        db.query(Address).filter(Address.user_id == user_id, Address.is_default == True).update({"is_default": False})
    address = Address(user_id=user_id, **kwargs)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def get_user_addresses(db: Session, user_id: int):
    return db.query(Address).filter(Address.user_id == user_id).all()


def get_address_by_id(db: Session, address_id: int):
    return db.query(Address).filter(Address.id == address_id).first()


def update_address(db: Session, address_id: int, **kwargs) -> Address | None:
    address = get_address_by_id(db, address_id)
    if not address:
        return None
    if kwargs.get("is_default"):
        db.query(Address).filter(
            Address.user_id == address.user_id, Address.id != address_id
        ).update({"is_default": False})
    for k, v in kwargs.items():
        if v is not None:
            setattr(address, k, v)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address_id: int) -> bool:
    address = get_address_by_id(db, address_id)
    if not address:
        return False
    db.delete(address)
    db.commit()
    return True
