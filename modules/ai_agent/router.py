from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from models import get_db, User
from config import SECRET_KEY, ALGORITHM
from modules.users.crud import get_user_by_id
from modules.ai_agent.schemas import AIChatRequest, AIChatResponse
from modules.ai_agent.agent import run_agent, get_or_create_session

router = APIRouter(prefix="/ai", tags=["AI Agent"])

# Опциональный заголовок Authorization (auto_error=False => без него тоже работает).
optional_api_key = APIKeyHeader(
    name="Authorization",
    description="Опционально: Bearer <ваш_токен>",
    auto_error=False,
)


def get_optional_user(
    authorization: Optional[str] = Depends(optional_api_key),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        return get_user_by_id(db, int(sub))
    except (JWTError, ValueError):
        return None


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    try:
        session = get_or_create_session(db, payload.session_id, user)
        result = run_agent(db, user, session, payload.message)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent error: {e}")
