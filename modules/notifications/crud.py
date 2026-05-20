from sqlalchemy.orm import Session
from models import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    body: str | None = None,
    type: NotificationType = NotificationType.system,
) -> Notification:
    n = Notification(user_id=user_id, title=title, body=body, type=type)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_user_notifications(db: Session, user_id: int, only_unread: bool = False):
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if only_unread:
        q = q.filter(Notification.is_read == False)
    return q.order_by(Notification.created_at.desc()).all()


def mark_read(db: Session, notification_id: int, user_id: int) -> Notification | None:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if not n:
        return None
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


def mark_all_read(db: Session, user_id: int):
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
