from pydantic import BaseModel
from datetime import datetime
from models import ReportStatus


class ReportCreate(BaseModel):
    target_type: str  # listing / user / review / shop
    target_id: int
    reason: str


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class ReportOut(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    status: ReportStatus
    created_at: datetime

    class Config:
        from_attributes = True
