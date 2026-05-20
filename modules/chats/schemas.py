from pydantic import BaseModel
from datetime import datetime


class ChatStartRequest(BaseModel):
    other_user_id: int


class ChatOut(BaseModel):
    id: int
    user_a_id: int
    user_b_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    text: str


class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
