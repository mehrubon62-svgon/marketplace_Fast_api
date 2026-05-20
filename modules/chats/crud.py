from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models import Chat, Message


def get_or_create_chat(db: Session, user_a_id: int, user_b_id: int) -> Chat:
    if user_a_id == user_b_id:
        raise ValueError("Cannot start chat with yourself")
    a, b = sorted([user_a_id, user_b_id])
    chat = (
        db.query(Chat)
        .filter(
            or_(
                and_(Chat.user_a_id == a, Chat.user_b_id == b),
                and_(Chat.user_a_id == b, Chat.user_b_id == a),
            )
        )
        .first()
    )
    if chat:
        return chat
    chat = Chat(user_a_id=a, user_b_id=b)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_user_chats(db: Session, user_id: int):
    return (
        db.query(Chat)
        .filter(or_(Chat.user_a_id == user_id, Chat.user_b_id == user_id))
        .order_by(Chat.created_at.desc())
        .all()
    )


def get_chat_by_id(db: Session, chat_id: int):
    return db.query(Chat).filter(Chat.id == chat_id).first()


def add_message(db: Session, chat_id: int, sender_id: int, text: str) -> Message:
    msg = Message(chat_id=chat_id, sender_id=sender_id, text=text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, chat_id: int):
    return (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .all()
    )


def mark_messages_read(db: Session, chat_id: int, reader_id: int):
    db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.sender_id != reader_id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()
