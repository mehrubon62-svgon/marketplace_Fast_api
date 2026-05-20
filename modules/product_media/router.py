from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Listing, ProductImage, ProductVariant
from modules.users.router import get_current_user
from modules.product_media.schemas import (
    ProductImageCreate,
    ProductImageOut,
    ProductVariantCreate,
    ProductVariantOut,
)
from modules.product_media.crud import (
    add_image,
    get_images,
    delete_image,
    add_variant,
    get_variants,
    delete_variant,
)

router = APIRouter(tags=["Product Media"])


def _check_listing_owner(db: Session, listing_id: int, user: User) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not your listing")
    return listing


# ---- Images ----
@router.get("/{listing_id}/images", response_model=list[ProductImageOut])
def list_images(listing_id: int, db: Session = Depends(get_db)):
    return get_images(db, listing_id)


@router.post("/{listing_id}/images", response_model=ProductImageOut)
def upload_image(
    listing_id: int,
    data: ProductImageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_listing_owner(db, listing_id, user)
    return add_image(db, listing_id, **data.model_dump())


@router.delete("/{listing_id}/images/{image_id}")
def remove_image(
    listing_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_listing_owner(db, listing_id, user)
    img = db.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.listing_id == listing_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    delete_image(db, image_id)
    return {"detail": "Image deleted"}


# ---- Variants ----
@router.get("/{listing_id}/variants", response_model=list[ProductVariantOut])
def list_variants(listing_id: int, db: Session = Depends(get_db)):
    return get_variants(db, listing_id)


@router.post("/{listing_id}/variants", response_model=ProductVariantOut)
def create_variant(
    listing_id: int,
    data: ProductVariantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_listing_owner(db, listing_id, user)
    return add_variant(db, listing_id, **data.model_dump())


@router.delete("/{listing_id}/variants/{variant_id}")
def remove_variant(
    listing_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_listing_owner(db, listing_id, user)
    v = db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.listing_id == listing_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Variant not found")
    delete_variant(db, variant_id)
    return {"detail": "Variant deleted"}
