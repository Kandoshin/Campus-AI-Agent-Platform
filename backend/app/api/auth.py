from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_optional_current_user, require_admin
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AdminCreateUserRequest, LoginRequest, LogoutResponse, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["Auth"])


def _public_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        is_guest=False,
    )


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id), role=user.role),
        user=_public_user(user),
    )


@router.post("/register")
def register_disabled():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="游客注册已关闭。如需注册请联系管理员：abc@example.com",
    )


@router.post("/users", response_model=UserPublic)
def create_user(
    request: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    existing_user = db.scalar(select(User).where(User.username == username))
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=username,
        display_name=request.display_name or username,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _public_user(user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == request.username.strip()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")

    return _token_response(user)


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser = Depends(get_optional_current_user)):
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        role=current_user.role,
        is_guest=current_user.is_guest,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout():
    return LogoutResponse()
