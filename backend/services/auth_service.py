import re

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.schemas import UserLoginRequest, UserPublic, UserRecord, UserRegisterRequest
from core.security import create_access_token, decode_access_token, hash_password, verify_password
from services.database_service import database_service


bearer_scheme = HTTPBearer(auto_error=False)


def public_user(user: UserRecord) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


class AuthService:
    def register(self, request: UserRegisterRequest) -> UserRecord:
        username = request.username.strip()
        email = request.email.strip().lower() if request.email else None
        if not re.fullmatch(r"[A-Za-z0-9_\-\u4e00-\u9fff]{3,50}", username):
            raise HTTPException(
                status_code=400,
                detail="用户名只能包含中文、字母、数字、下划线和短横线，长度 3-50",
            )
        if email == "":
            email = None
        password_hash = hash_password(request.password)
        return database_service.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
        )

    def login(self, request: UserLoginRequest) -> tuple[str, UserRecord]:
        user = database_service.get_user_by_login(request.username_or_email)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="密码错误")
        token = create_access_token(str(user.id))
        return token, user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或 token 失效",
        )
    subject = decode_access_token(credentials.credentials)
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或 token 失效",
        ) from exc
    user = database_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或 token 失效",
        )
    return user


auth_service = AuthService()
