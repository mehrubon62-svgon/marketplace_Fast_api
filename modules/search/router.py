from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models import get_db, Listing, Category
from modules.listings.schemas import ListingOut

router = APIRouter(prefix="/search", tags=["Search"])


def _expand_category_ids(db: Session, root_id: int) -> list[int]:
    """Возвращает id категории + всех её потомков рекурсивно."""
    ids = {root_id}
    queue = [root_id]
    while queue:
        parent = queue.pop()
        children = db.query(Category).filter(Category.parent_id == parent).all()
        for c in children:
            if c.id not in ids:
                ids.add(c.id)
                queue.append(c.id)
    return list(ids)


@router.get("/", response_model=list[ListingOut])
def search_listings(
    q: str = Query(default=""),
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = Query(default="newest", pattern="^(newest|cheapest|expensive)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).filter(Listing.is_active == True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Listing.title.ilike(like)) | (Listing.description.ilike(like))
        )

    if category_id:
        ids = _expand_category_ids(db, category_id)
        query = query.filter(Listing.category_id.in_(ids))

    if min_price is not None:
        query = query.filter(Listing.price >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    if sort_by == "cheapest":
        query = query.order_by(Listing.price.asc())
    elif sort_by == "expensive":
        query = query.order_by(Listing.price.desc())
    else:
        query = query.order_by(Listing.created_at.desc())

    return query.offset(offset).limit(limit).all()
