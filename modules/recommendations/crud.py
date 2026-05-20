from sqlalchemy.orm import Session
from typing import List

from models import Listing
from modules.recommendations.embeddings import (
    encode_text,
    cosine_similarity,
    build_listing_text,
)


def ensure_embedding(db: Session, listing: Listing) -> Listing:
    """Посчитать и сохранить embedding для товара, если его ещё нет."""
    if listing.embedding:
        return listing
    text = build_listing_text(listing.title, listing.description)
    listing.embedding = encode_text(text)
    db.commit()
    db.refresh(listing)
    return listing


def reindex_all(db: Session) -> int:
    """Пересчитать embeddings для всех товаров. Возвращает количество обработанных."""
    listings = db.query(Listing).all()
    count = 0
    for l in listings:
        text = build_listing_text(l.title, l.description)
        l.embedding = encode_text(text)
        count += 1
    db.commit()
    return count


def find_similar(db: Session, listing_id: int, limit: int = 10) -> List[dict]:
    """
    Найти похожие товары по embedding текстового описания.
    Похожесть считается через cosine similarity.
    """
    target = db.query(Listing).filter(Listing.id == listing_id).first()
    if not target:
        return []

    ensure_embedding(db, target)

    candidates = (
        db.query(Listing)
        .filter(Listing.id != listing_id, Listing.is_active == True)
        .all()
    )

    scored = []
    for cand in candidates:
        if not cand.embedding:
            ensure_embedding(db, cand)
        score = cosine_similarity(target.embedding, cand.embedding or [])
        # лёгкий бонус за совпадение категории
        if cand.category_id == target.category_id:
            score += 0.05
        scored.append((cand, score))

    scored.sort(key=lambda x: -x[1])
    top = scored[:limit]

    return [
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
            "image_url": l.image_url,
            "category_id": l.category_id,
            "score": round(score, 4),
        }
        for l, score in top
    ]


def search_by_query(db: Session, query: str, limit: int = 10) -> List[dict]:
    """Семантический поиск товаров по произвольному запросу."""
    if not query.strip():
        return []
    q_embedding = encode_text(query)

    candidates = db.query(Listing).filter(Listing.is_active == True).all()
    scored = []
    for cand in candidates:
        if not cand.embedding:
            ensure_embedding(db, cand)
        score = cosine_similarity(q_embedding, cand.embedding or [])
        scored.append((cand, score))

    scored.sort(key=lambda x: -x[1])
    top = scored[:limit]
    return [
        {
            "id": l.id,
            "title": l.title,
            "price": l.price,
            "image_url": l.image_url,
            "category_id": l.category_id,
            "score": round(score, 4),
        }
        for l, score in top
    ]
