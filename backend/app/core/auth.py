from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

UserRole = Literal["guest", "student", "admin"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: int | None
    username: str
    display_name: str
    role: UserRole
    is_guest: bool = False


GUEST_USER = CurrentUser(
    id=None,
    username="guest",
    display_name="访客",
    role="guest",
    is_guest=True,
)


def _to_current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,  # type: ignore[arg-type]
        is_guest=False,
    )


def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not token:
        return GUEST_USER

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as exc:
        raise credentials_error from exc

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise credentials_error

    return _to_current_user(user)


def get_current_user(user: CurrentUser = Depends(get_optional_current_user)) -> CurrentUser:
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
