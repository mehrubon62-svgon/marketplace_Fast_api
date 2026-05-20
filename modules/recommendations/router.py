from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from models import get_db, User
from modules.users.router import require_admin
from modules.recommendations.schemas import SimilarListingOut, SemanticSearchRequest
from modules.recommendations.crud import find_similar, reindex_all, search_by_query

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/similar/{listing_id}", response_model=List[SimilarListingOut])
def get_similar(listing_id: int, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    items = find_similar(db, listing_id, limit)
    if not items:
        raise HTTPException(status_code=404, detail="Listing not found or no similar items")
    return items


@router.post("/search", response_model=List[SimilarListingOut])
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db)):
    items = search_by_query(db, payload.query, payload.limit)
    return items


@router.post("/reindex")
def reindex(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Пересчитать embeddings для всех товаров (админ)."""
    count = reindex_all(db)
    return {"reindexed": count}
