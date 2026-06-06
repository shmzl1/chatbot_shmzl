import re

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.schemas import UserLoginRequest, UserPublic, UserRecord, UserSetupRequest
from core.security import create_access_token, decode_access_token, hash_password, verify_password
from services.database_service import database_service


bearer_scheme = HTTPBearer(auto_error=False)
MAX_PASSWORD_CHARS = 1024
MIN_PASSWORD_CHARS = 6


def public_user(user: UserRecord) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


class AuthService:
    def has_user(self) -> bool:
        count = database_service.user_count()
        if count > 1:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Duplicate local users found. This project supports exactly one "
                    "local user; please inspect the users table and manually resolve duplicates."
                ),
            )
        return count > 0

    def setup(self, request: UserSetupRequest) -> tuple[str, UserRecord]:
        if self.has_user():
            raise HTTPException(status_code=409, detail="本地账号已初始化")
        username = self._clean_username(request.username)
        password = self._clean_setup_password(request.password)
        password_hash = hash_password(password)
        user = database_service.create_user(
            username=username,
            email=None,
            password_hash=password_hash,
        )
        token = create_access_token(str(user.id))
        return token, user

    def login(self, request: UserLoginRequest) -> tuple[str, UserRecord]:
        if not self.has_user():
            raise HTTPException(status_code=400, detail="账号未初始化")
        username = request.username.strip()
        password = self._clean_login_password(request.password)
        user = database_service.get_user_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = create_access_token(str(user.id))
        return token, user

    def _clean_username(self, username: str) -> str:
        value = username.strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-\u4e00-\u9fff]{3,50}", value):
            raise HTTPException(
                status_code=400,
                detail="用户名只能包含中文、字母、数字、下划线和短横线，长度 3-50",
            )
        return value

    def _clean_setup_password(self, password: str) -> str:
        value = self._clean_login_password(password)
        if len(value) < MIN_PASSWORD_CHARS:
            raise HTTPException(status_code=400, detail="密码至少需要 6 个字符")
        return value

    def _clean_login_password(self, password: str) -> str:
        if not password:
            raise HTTPException(status_code=400, detail="密码不能为空")
        if len(password) > MAX_PASSWORD_CHARS:
            raise HTTPException(status_code=400, detail="密码过长，请控制在 1024 个字符以内")
        return password


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        )
    subject = decode_access_token(credentials.credentials)
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        ) from exc
    user = database_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        )
    return user


auth_service = AuthService()
