import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import bcrypt

from models import User, RoleEnum, RefreshToken, UserProfile, Wallet
from config import REFRESH_TOKEN_EXPIRE_DAYS


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, email: str, password: str, role: RoleEnum = RoleEnum.user):
    hashed = hash_password(password)
    user = User(username=username, email=email, hashed_password=hashed, role=role)
    db.add(user)
    db.flush()
    # Автосоздание кошелька с балансом 0
    wallet = Wallet(user_id=user.id, balance=0.0)
    db.add(wallet)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session):
    return db.query(User).all()


# ------ Refresh tokens ------
def create_refresh_token(db: Session, user_id: int) -> RefreshToken:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_refresh_token(db: Session, token: str):
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def revoke_refresh_token(db: Session, token: str) -> bool:
    rt = get_refresh_token(db, token)
    if not rt:
        return False
    rt.revoked = True
    db.commit()
    return True


def revoke_all_user_tokens(db: Session, user_id: int):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id, RefreshToken.revoked == False
    ).update({"revoked": True})
    db.commit()


# ------ Profile ------
def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, user_id: int, **kwargs) -> UserProfile:
    profile = get_or_create_profile(db, user_id)
    for k, v in kwargs.items():
        if v is not None:
            setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile
