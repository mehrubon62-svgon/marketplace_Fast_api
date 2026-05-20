from pydantic import BaseModel
from datetime import datetime
from models import NotificationType


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType = NotificationType.system
    title: str
    body: str | None = None


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    body: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
