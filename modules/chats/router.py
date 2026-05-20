from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user
from modules.users.crud import get_user_by_id
from modules.chats.schemas import ChatStartRequest, ChatOut, MessageCreate, MessageOut
from modules.chats.crud import (
    get_or_create_chat,
    get_user_chats,
    get_chat_by_id,
    add_message,
    get_messages,
    mark_messages_read,
)
from modules.notifications.crud import create_notification
from modules.websockets.manager import manager
from models import NotificationType

router = APIRouter(prefix="/chats", tags=["Chats"])


def _check_chat_access(chat, user: User):
    if chat.user_a_id != user.id and chat.user_b_id != user.id:
        raise HTTPException(status_code=403, detail="Not your chat")


@router.post("/start", response_model=ChatOut)
def start_chat(
    data: ChatStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not get_user_by_id(db, data.other_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return get_or_create_chat(db, user.id, data.other_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ChatOut])
def list_my_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_user_chats(db, user.id)


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def list_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _check_chat_access(chat, user)
    mark_messages_read(db, chat_id, user.id)
    return get_messages(db, chat_id)


@router.post("/{chat_id}/messages", response_model=MessageOut)
async def send_message(
    chat_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _check_chat_access(chat, user)
    msg = add_message(db, chat_id, user.id, data.text)

    recipient_id = chat.user_b_id if chat.user_a_id == user.id else chat.user_a_id
    preview = data.text if len(data.text) <= 80 else data.text[:77] + "..."
    create_notification(
        db,
        user_id=recipient_id,
        title=f"Новое сообщение от {user.username}",
        body=preview,
        type=NotificationType.chat,
    )
    await manager.send_personal(recipient_id, {
        "event": "new_message",
        "chat_id": chat_id,
        "sender_id": user.id,
        "sender_username": user.username,
        "text": data.text,
        "message_id": msg.id,
    })
    return msg
