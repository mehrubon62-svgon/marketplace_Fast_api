from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user
from modules.addresses.schemas import AddressCreate, AddressUpdate, AddressOut
from modules.addresses.crud import (
    create_address,
    get_user_addresses,
    get_address_by_id,
    update_address,
    delete_address,
)

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("/", response_model=AddressOut)
def add_address(data: AddressCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_address(db, user.id, **data.model_dump())


@router.get("/", response_model=list[AddressOut])
def list_my_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_user_addresses(db, user.id)


@router.get("/{address_id}", response_model=AddressOut)
def get_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.put("/{address_id}", response_model=AddressOut)
def edit_address(
    address_id: int,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(status_code=404, detail="Address not found")
    return update_address(db, address_id, **data.model_dump(exclude_unset=True))


@router.delete("/{address_id}")
def remove_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address = get_address_by_id(db, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(status_code=404, detail="Address not found")
    delete_address(db, address_id)
    return {"detail": "Address deleted"}
