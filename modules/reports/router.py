from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, ReportStatus
from modules.users.router import get_current_user, require_admin
from modules.reports.schemas import ReportCreate, ReportStatusUpdate, ReportOut
from modules.reports.crud import (
    create_report,
    get_all_reports,
    get_report_by_id,
    update_report_status,
    ALLOWED_TARGETS,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportOut)
def submit_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.target_type not in ALLOWED_TARGETS:
        raise HTTPException(
            status_code=400,
            detail=f"target_type must be one of {sorted(ALLOWED_TARGETS)}",
        )
    return create_report(db, user.id, data.target_type, data.target_id, data.reason)


@router.get("/", response_model=list[ReportOut])
def list_reports(
    status: ReportStatus | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return get_all_reports(db, status)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    r = get_report_by_id(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


@router.patch("/{report_id}/status", response_model=ReportOut)
def change_report_status(
    report_id: int,
    data: ReportStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    r = update_report_status(db, report_id, data.status)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r
