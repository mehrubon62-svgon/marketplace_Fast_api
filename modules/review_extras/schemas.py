from pydantic import BaseModel
from datetime import datetime


class ReviewReplyCreate(BaseModel):
    text: str


class ReviewReplyOut(BaseModel):
    id: int
    review_id: int
    author_id: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewImageCreate(BaseModel):
    url: str


class ReviewImageOut(BaseModel):
    id: int
    review_id: int
    url: str

    class Config:
        from_attributes = True


class ReviewVoteRequest(BaseModel):
    is_helpful: bool = True


class ReviewVoteOut(BaseModel):
    id: int
    review_id: int
    user_id: int
    is_helpful: bool

    class Config:
        from_attributes = True
