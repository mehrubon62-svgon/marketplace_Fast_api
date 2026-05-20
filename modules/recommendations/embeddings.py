"""
Локальные текстовые embeddings через sentence-transformers.
Модель загружается лениво (один раз при первом обращении).
"""
from typing import List, Optional
import numpy as np

from config import EMBEDDING_MODEL

_model = None


def get_model():
    global _model
    if _model is None:
        # Импорт внутри функции, чтобы тяжёлая зависимость грузилась лениво
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def encode_text(text: str) -> List[float]:
    """Получить embedding текста как python list (для сохранения в JSON)."""
    if not text or not text.strip():
        return []
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    va = np.array(a)
    vb = np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def build_listing_text(title: Optional[str], description: Optional[str]) -> str:
    parts = [p for p in (title, description) if p]
    return " | ".join(parts)
