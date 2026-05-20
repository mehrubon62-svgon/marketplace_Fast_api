from sqlalchemy.orm import Session
from models import Brand


def create_brand(db: Session, name: str, logo_url: str | None = None) -> Brand:
    brand = Brand(name=name, logo_url=logo_url)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def get_all_brands(db: Session):
    return db.query(Brand).all()


def get_brand_by_id(db: Session, brand_id: int):
    return db.query(Brand).filter(Brand.id == brand_id).first()


def delete_brand(db: Session, brand_id: int) -> bool:
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        return False
    db.delete(brand)
    db.commit()
    return True
