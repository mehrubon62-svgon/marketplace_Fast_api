from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user
from modules.favorites.schemas import FavoriteAdd, FavoriteOut
from modules.favorites.crud import get_favorites, add_favorite, remove_favorite

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/", response_model=list[FavoriteOut])
def my_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_favorites(db, current_user.id)


@router.post("/", response_model=FavoriteOut)
def add_to_favorites(data: FavoriteAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return add_favorite(db, current_user.id, data.listing_id)


@router.delete("/{listing_id}")
def remove_from_favorites(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fav = remove_favorite(db, current_user.id, listing_id)
    if not fav:
        raise HTTPException(status_code=404, detail="Not in favorites")
    return {"detail": "Removed from favorites"}
