from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Order
from modules.users.router import get_current_user, require_admin
from modules.shipments.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentOut,
    DeliveryMethodCreate,
    DeliveryMethodOut,
)
from modules.shipments.crud import (
    create_shipment,
    get_shipment_by_order,
    update_shipment,
    create_delivery_method,
    get_all_delivery_methods,
    delete_delivery_method,
)

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.post("/", response_model=ShipmentOut)
def create(
    data: ShipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.seller_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only seller can create shipment")
    if order.shipment:
        raise HTTPException(status_code=400, detail="Shipment already exists for this order")
    return create_shipment(db, **data.model_dump())


@router.get("/order/{order_id}", response_model=ShipmentOut)
def get_by_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shipment = get_shipment_by_order(db, order_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if (
        shipment.order.buyer_id != user.id
        and shipment.order.seller_id != user.id
        and user.role.value != "admin"
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    return shipment


@router.patch("/{shipment_id}", response_model=ShipmentOut)
def edit(
    shipment_id: int,
    data: ShipmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from models import Shipment

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if shipment.order.seller_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    return update_shipment(db, shipment_id, **data.model_dump(exclude_unset=True))


# ---- Delivery methods ----
@router.get("/delivery-methods", response_model=list[DeliveryMethodOut])
def list_delivery_methods(db: Session = Depends(get_db)):
    return get_all_delivery_methods(db)


@router.post("/delivery-methods", response_model=DeliveryMethodOut)
def add_delivery_method(
    data: DeliveryMethodCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return create_delivery_method(db, **data.model_dump())


@router.delete("/delivery-methods/{dm_id}")
def remove_delivery_method(dm_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not delete_delivery_method(db, dm_id):
        raise HTTPException(status_code=404, detail="Delivery method not found")
    return {"detail": "Deleted"}
