from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, ShopStatus
from modules.users.router import get_current_user
from modules.listings.schemas import ListingCreate, ListingUpdate, ListingOut
from modules.listings.crud import (
    create_listing,
    get_all_listings,
    get_listings_by_category,
    get_listings_by_owner,
    get_listing_by_id,
    update_listing,
    delete_listing,
)
from modules.cache.redis_client import get_cached, set_cached, delete_cached

router = APIRouter(prefix="/listings", tags=["Listings"])


def require_approved_shop(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.shop or current_user.shop.status != ShopStatus.approved:
        raise HTTPException(status_code=403, detail="You need an approved shop to create listings")
    return current_user


@router.post("/", response_model=ListingOut)
async def add_listing(data: ListingCreate, db: Session = Depends(get_db), current_user: User = Depends(require_approved_shop)):
    listing = create_listing(
        db,
        title=data.title,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        category_id=data.category_id,
        owner_id=current_user.id,
        brand_id=data.brand_id,
    )
    await delete_cached("listings:*")
    return listing


@router.get("/", response_model=list[ListingOut])
async def list_all_listings(db: Session = Depends(get_db), category_id: int | None = None):
    cache_key = f"listings:all:cat={category_id or 'all'}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    if category_id:
        listings = get_listings_by_category(db, category_id)
    else:
        listings = get_all_listings(db)
    out = [ListingOut.model_validate(l).model_dump() for l in listings]
    await set_cached(cache_key, out, ttl=30)
    return out


@router.get("/my", response_model=list[ListingOut])
def list_my_listings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_listings_by_owner(db, current_user.id)


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.put("/{listing_id}", response_model=ListingOut)
async def edit_listing(
    listing_id: int,
    data: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_shop),
):
    listing = get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your listing")
    updated = update_listing(db, listing_id, **data.model_dump(exclude_unset=True))
    await delete_cached("listings:*")
    return updated


@router.delete("/{listing_id}")
async def remove_listing(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    delete_listing(db, listing_id)
    await delete_cached("listings:*")
    return {"detail": "Listing deleted"}
