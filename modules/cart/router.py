from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user
from modules.cart.schemas import CartItemAdd, CartItemUpdate, CartItemOut
from modules.cart.crud import get_cart_items, add_to_cart, update_cart_item_quantity, remove_from_cart, clear_cart
from modules.listings.crud import get_listing_by_id

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=list[CartItemOut])
def get_my_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_cart_items(db, current_user.id)


@router.post("/", response_model=CartItemOut)
def add_item_to_cart(data: CartItemAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = get_listing_by_id(db, data.listing_id)
    if not listing or not listing.is_active:
        raise HTTPException(status_code=404, detail="Listing not found or inactive")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add your own listing to cart")
    if data.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")
    return add_to_cart(db, current_user.id, data.listing_id, data.quantity)


@router.delete("/clear")
def clear_my_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clear_cart(db, current_user.id)
    return {"detail": "Cart cleared"}


@router.patch("/{item_id}", response_model=CartItemOut | None)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = update_cart_item_quantity(db, item_id, current_user.id, data.quantity)
    if item is None and data.quantity > 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return item


@router.delete("/{item_id}")
def delete_cart_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = remove_from_cart(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"detail": "Removed from cart"}
