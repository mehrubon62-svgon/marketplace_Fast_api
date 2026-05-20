"""
WebSocket endpoints.
Клиент подключается к /ws?token=<JWT>.
Сервер пушит уведомления (заказы, чаты, баланс).
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from models import get_db, User
from config import SECRET_KEY, ALGORITHM
from modules.users.crud import get_user_by_id
from modules.websockets.manager import manager

router = APIRouter(tags=["WebSocket"])


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            return None
        return get_user_by_id(db, int(sub))
    except (JWTError, ValueError):
        return None


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    Подключение: ws://host/ws?token=<jwt>
    Получает события: new_order, order_status_changed, new_message, wallet_topup.
    """
    user = _user_from_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)
    try:
        # Приветствие
        await websocket.send_json({"event": "connected", "user_id": user.id})
        # Держим соединение, можно слушать ping или текстовые команды от клиента
        while True:
            data = await websocket.receive_text()
            # эхо для проверки живости
            await websocket.send_json({"event": "ack", "echo": data})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user.id)
    except Exception:
        await manager.disconnect(websocket, user.id)
