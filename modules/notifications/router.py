from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user, require_admin
from modules.notifications.schemas import NotificationCreate, NotificationOut
from modules.notifications.crud import (
    create_notification,
    get_user_notifications,
    mark_read,
    mark_all_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationOut])
def list_notifications(
    only_unread: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_user_notifications(db, user.id, only_unread)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_one_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = mark_read(db, notification_id, user.id)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    return n


@router.post("/read-all")
def mark_everything_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mark_all_read(db, user.id)
    return {"detail": "All notifications marked as read"}


@router.post("/admin/create", response_model=NotificationOut)
def admin_create(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return create_notification(db, data.user_id, data.title, data.body, data.type)
