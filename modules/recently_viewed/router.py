from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Listing
from modules.users.router import get_current_user
from modules.recently_viewed.schemas import RecentlyViewedOut
from modules.recently_viewed.crud import track_view, get_recent

router = APIRouter(prefix="/recently-viewed", tags=["Recently Viewed"])


@router.post("/{listing_id}", response_model=RecentlyViewedOut)
def track(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Listing).filter(Listing.id == listing_id).first():
        raise HTTPException(status_code=404, detail="Listing not found")
    return track_view(db, user.id, listing_id)


@router.get("/", response_model=list[RecentlyViewedOut])
def list_recent(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_recent(db, user.id, limit)
