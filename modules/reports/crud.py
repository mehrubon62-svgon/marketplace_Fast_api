from sqlalchemy.orm import Session
from models import Report, ReportStatus

ALLOWED_TARGETS = {"listing", "user", "review", "shop"}


def create_report(db: Session, reporter_id: int, target_type: str, target_id: int, reason: str) -> Report:
    r = Report(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_all_reports(db: Session, status: ReportStatus | None = None):
    q = db.query(Report)
    if status:
        q = q.filter(Report.status == status)
    return q.order_by(Report.created_at.desc()).all()


def get_report_by_id(db: Session, report_id: int):
    return db.query(Report).filter(Report.id == report_id).first()


def update_report_status(db: Session, report_id: int, status: ReportStatus):
    r = get_report_by_id(db, report_id)
    if not r:
        return None
    r.status = status
    db.commit()
    db.refresh(r)
    return r
