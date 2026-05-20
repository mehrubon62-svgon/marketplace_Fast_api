from sqlalchemy.orm import Session

from models import Listing


# Поля, изменение которых должно сбросить embedding
EMBEDDING_AFFECTING_FIELDS = {"title", "description"}


def create_listing(
    db: Session,
    title: str,
    description: str | None,
    price: float,
    image_url: str | None,
    category_id: int,
    owner_id: int,
    brand_id: int | None = None,
):
    listing = Listing(
        title=title,
        description=description,
        price=price,
        image_url=image_url,
        category_id=category_id,
        owner_id=owner_id,
        brand_id=brand_id,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_all_listings(db: Session):
    return db.query(Listing).filter(Listing.is_active == True).all()


def get_listings_by_category(db: Session, category_id: int):
    """Возвращает товары категории, включая все её подкатегории (рекурсивно)."""
    from models import Category

    # собираем id категории и её потомков
    ids = {category_id}
    queue = [category_id]
    while queue:
        parent = queue.pop()
        children = db.query(Category).filter(Category.parent_id == parent).all()
        for c in children:
            if c.id not in ids:
                ids.add(c.id)
                queue.append(c.id)

    return (
        db.query(Listing)
        .filter(Listing.category_id.in_(ids), Listing.is_active == True)
        .all()
    )


def get_listings_by_owner(db: Session, owner_id: int):
    return db.query(Listing).filter(Listing.owner_id == owner_id).all()


def get_listing_by_id(db: Session, listing_id: int):
    return db.query(Listing).filter(Listing.id == listing_id).first()


def update_listing(db: Session, listing_id: int, **kwargs):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return None

    embedding_dirty = False
    for key, value in kwargs.items():
        if value is not None:
            setattr(listing, key, value)
            if key in EMBEDDING_AFFECTING_FIELDS:
                embedding_dirty = True

    if embedding_dirty:
        listing.embedding = None  # будет пересчитан по запросу

    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing_id: int):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if listing:
        db.delete(listing)
        db.commit()
    return listing
