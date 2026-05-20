from sqlalchemy.orm import Session
from models import ProductImage, ProductVariant, Listing


def add_image(db: Session, listing_id: int, **kwargs) -> ProductImage:
    if kwargs.get("is_primary"):
        db.query(ProductImage).filter(
            ProductImage.listing_id == listing_id,
            ProductImage.is_primary == True,
        ).update({"is_primary": False})
    image = ProductImage(listing_id=listing_id, **kwargs)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_images(db: Session, listing_id: int):
    return (
        db.query(ProductImage)
        .filter(ProductImage.listing_id == listing_id)
        .order_by(ProductImage.sort_order)
        .all()
    )


def delete_image(db: Session, image_id: int) -> ProductImage | None:
    img = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if not img:
        return None
    db.delete(img)
    db.commit()
    return img


def add_variant(db: Session, listing_id: int, **kwargs) -> ProductVariant:
    variant = ProductVariant(listing_id=listing_id, **kwargs)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def get_variants(db: Session, listing_id: int):
    return db.query(ProductVariant).filter(ProductVariant.listing_id == listing_id).all()


def delete_variant(db: Session, variant_id: int) -> ProductVariant | None:
    v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not v:
        return None
    db.delete(v)
    db.commit()
    return v
