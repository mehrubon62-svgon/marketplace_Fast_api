from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from models import get_db, User, RoleEnum
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from modules.users.schemas import (
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    RefreshRequest,
    ProfileOut,
    ProfileUpdate,
)
from modules.users.crud import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    verify_password,
    get_all_users,
    get_user_by_id,
    create_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    get_or_create_profile,
    update_profile,
)
from fastapi.security import APIKeyHeader

router = APIRouter(prefix="/users", tags=["Users"])

api_key_scheme = APIKeyHeader(
    name="Authorization",
    description="Введите: Bearer <ваш_токен>",
    auto_error=True,
)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _extract_token(value: str) -> str:
    """Из строки 'Bearer xxx' достать сам токен. Кидает 401 если формат неверный."""
    if not value:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = value.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header. Expected: 'Bearer <token>'",
        )
    return parts[1].strip()


def get_current_user(
    authorization: str = Depends(api_key_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _extract_token(authorization)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/register", response_model=Token, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.
    Возвращает сразу access + refresh токены — можно копировать access_token
    и нажимать кнопку Authorize вверху Swagger.
    """
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, data.username, data.email, data.password)
    access_token = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token(db, user.id)
    return {"access_token": access_token, "refresh_token": refresh.token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_username(db, data.username)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token(db, user.id)
    return {"access_token": access_token, "refresh_token": refresh.token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    rt = get_refresh_token(db, payload.refresh_token)
    if not rt or rt.revoked:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    now_naive = datetime.utcnow()
    expires_at = rt.expires_at.replace(tzinfo=None) if rt.expires_at.tzinfo else rt.expires_at
    if expires_at < now_naive:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = get_user_by_id(db, rt.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": rt.token, "token_type": "bearer"}


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    revoke_refresh_token(db, payload.refresh_token)
    return {"detail": "Logged out"}


@router.post("/logout-all")
def logout_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    revoke_all_user_tokens(db, user.id)
    return {"detail": "All sessions revoked"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/profile", response_model=ProfileOut)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_or_create_profile(db, user.id)


@router.put("/me/profile", response_model=ProfileOut)
def edit_my_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return update_profile(db, user.id, **data.model_dump(exclude_unset=True))


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return get_all_users(db)
