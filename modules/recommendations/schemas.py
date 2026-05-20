from pydantic import BaseModel
from typing import Optional


class SimilarListingOut(BaseModel):
    id: int
    title: str
    price: float
    image_url: Optional[str] = None
    category_id: int
    score: float


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
