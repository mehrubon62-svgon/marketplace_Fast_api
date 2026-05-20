from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Banner, FlashSale, Listing


# ---- Banners ----
def create_banner(db: Session, **kwargs) -> Banner:
    b = Banner(**kwargs)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def get_active_banners(db: Session):
    return db.query(Banner).filter(Banner.is_active == True).order_by(Banner.sort_order).all()


def delete_banner(db: Session, banner_id: int) -> bool:
    b = db.query(Banner).filter(Banner.id == banner_id).first()
    if not b:
        return False
    db.delete(b)
    db.commit()
    return True


# ---- Flash sales ----
def create_flash_sale(
    db: Session,
    listing_ids: list[int],
    discount_percent: float,
    starts_at: datetime,
    ends_at: datetime,
    title: str | None = None,
) -> FlashSale:
    listings = db.query(Listing).filter(Listing.id.in_(listing_ids)).all()
    fs = FlashSale(
        title=title,
        discount_percent=discount_percent,
        starts_at=starts_at,
        ends_at=ends_at,
        listings=listings,
    )
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs


def get_flash_sale_by_id(db: Session, fs_id: int) -> FlashSale | None:
    return db.query(FlashSale).filter(FlashSale.id == fs_id).first()


def get_active_flash_sales(db: Session):
    now = datetime.utcnow()
    return (
        db.query(FlashSale)
        .filter(
            and_(
                FlashSale.is_active == True,
                FlashSale.starts_at <= now,
                FlashSale.ends_at >= now,
            )
        )
        .order_by(FlashSale.starts_at.desc())
        .all()
    )


def get_all_flash_sales(db: Session):
    return db.query(FlashSale).order_by(FlashSale.starts_at.desc()).all()


def update_flash_sale(db: Session, fs_id: int, **kwargs) -> FlashSale | None:
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(fs, k, v)
    db.commit()
    db.refresh(fs)
    return fs


def set_flash_sale_listings(db: Session, fs_id: int, listing_ids: list[int]) -> FlashSale | None:
    """Полностью заменить список товаров в акции."""
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        return None
    listings = db.query(Listing).filter(Listing.id.in_(listing_ids)).all()
    fs.listings = listings
    db.commit()
    db.refresh(fs)
    return fs


def add_listings_to_flash_sale(db: Session, fs_id: int, listing_ids: list[int]) -> FlashSale | None:
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        return None
    existing_ids = {l.id for l in fs.listings}
    to_add = db.query(Listing).filter(Listing.id.in_([i for i in listing_ids if i not in existing_ids])).all()
    fs.listings.extend(to_add)
    db.commit()
    db.refresh(fs)
    return fs


def remove_listing_from_flash_sale(db: Session, fs_id: int, listing_id: int) -> FlashSale | None:
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        return None
    fs.listings = [l for l in fs.listings if l.id != listing_id]
    db.commit()
    db.refresh(fs)
    return fs


def deactivate_flash_sale(db: Session, fs_id: int) -> bool:
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        return False
    fs.is_active = False
    db.commit()
    return True
