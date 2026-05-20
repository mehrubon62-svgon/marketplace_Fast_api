from sqlalchemy.orm import Session
from models import Tag, Listing


def create_tag(db: Session, name: str) -> Tag:
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def get_all_tags(db: Session):
    return db.query(Tag).all()


def get_tag_by_id(db: Session, tag_id: int):
    return db.query(Tag).filter(Tag.id == tag_id).first()


def delete_tag(db: Session, tag_id: int) -> bool:
    tag = get_tag_by_id(db, tag_id)
    if not tag:
        return False
    db.delete(tag)
    db.commit()
    return True


def attach_tag(db: Session, listing: Listing, tag: Tag):
    if tag not in listing.tags:
        listing.tags.append(tag)
        db.commit()


def detach_tag(db: Session, listing: Listing, tag: Tag):
    if tag in listing.tags:
        listing.tags.remove(tag)
        db.commit()
