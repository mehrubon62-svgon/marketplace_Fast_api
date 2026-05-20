from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Listing
from modules.users.router import get_current_user, require_admin
from modules.tags.schemas import TagCreate, TagOut
from modules.tags.crud import (
    create_tag,
    get_all_tags,
    get_tag_by_id,
    delete_tag,
    attach_tag,
    detach_tag,
)

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return get_all_tags(db)


@router.post("/", response_model=TagOut)
def add_tag(data: TagCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return create_tag(db, data.name)


@router.delete("/{tag_id}")
def remove_tag(tag_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not delete_tag(db, tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted"}


@router.post("/listings/{listing_id}/{tag_id}")
def add_tag_to_listing(
    listing_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    tag = get_tag_by_id(db, tag_id)
    if not listing or not tag:
        raise HTTPException(status_code=404, detail="Listing or tag not found")
    if listing.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    attach_tag(db, listing, tag)
    return {"detail": "Tag attached"}


@router.delete("/listings/{listing_id}/{tag_id}")
def remove_tag_from_listing(
    listing_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    tag = get_tag_by_id(db, tag_id)
    if not listing or not tag:
        raise HTTPException(status_code=404, detail="Listing or tag not found")
    if listing.owner_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    detach_tag(db, listing, tag)
    return {"detail": "Tag detached"}
