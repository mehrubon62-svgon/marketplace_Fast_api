from sqlalchemy.orm import Session

from models import Category


def create_category(db: Session, name: str, parent_id: int | None = None):
    category = Category(name=name, parent_id=parent_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_all_categories(db: Session):
    return db.query(Category).all()


def get_category_by_id(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_name(db: Session, name: str):
    return db.query(Category).filter(Category.name == name).first()


def delete_category(db: Session, category_id: int):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
    return category
