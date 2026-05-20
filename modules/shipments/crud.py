from sqlalchemy.orm import Session
from models import Shipment, DeliveryMethod


def create_shipment(db: Session, **kwargs) -> Shipment:
    shipment = Shipment(**kwargs)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def get_shipment_by_order(db: Session, order_id: int):
    return db.query(Shipment).filter(Shipment.order_id == order_id).first()


def update_shipment(db: Session, shipment_id: int, **kwargs):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(shipment, k, v)
    db.commit()
    db.refresh(shipment)
    return shipment


# delivery methods
def create_delivery_method(db: Session, **kwargs) -> DeliveryMethod:
    dm = DeliveryMethod(**kwargs)
    db.add(dm)
    db.commit()
    db.refresh(dm)
    return dm


def get_all_delivery_methods(db: Session):
    return db.query(DeliveryMethod).filter(DeliveryMethod.is_active == True).all()


def delete_delivery_method(db: Session, dm_id: int) -> bool:
    dm = db.query(DeliveryMethod).filter(DeliveryMethod.id == dm_id).first()
    if not dm:
        return False
    db.delete(dm)
    db.commit()
    return True
