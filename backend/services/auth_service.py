from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.schemas import UserLoginRequest, UserPublic, UserRecord, UserSetupRequest
from services.database_service import database_service


bearer_scheme = HTTPBearer(auto_error=False)
DEFAULT_LOCAL_USERNAME = "我"
DEFAULT_LOCAL_EMAIL = None
DEFAULT_LOCAL_PASSWORD_HASH = ""


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
        return self.get_default_user() is not None

    def ensure_default_user(self) -> UserRecord:
        user = database_service.get_single_user()
        if user:
            return user
        return database_service.create_user(
            username=DEFAULT_LOCAL_USERNAME,
            email=DEFAULT_LOCAL_EMAIL,
            password_hash=DEFAULT_LOCAL_PASSWORD_HASH,
        )

    def get_default_user(self) -> UserRecord:
        return self.ensure_default_user()

    def update_default_user_profile(self, username: str | None = None) -> UserRecord:
        user = self.get_default_user()
        if username is None:
            return user
        return database_service.update_user_profile(user.id, self._clean_username(username))

    def setup(self, request: UserSetupRequest) -> tuple[str, UserRecord]:
        user = self.ensure_default_user()
        if request.username:
            user = self.update_default_user_profile(request.username)
        return "", user

    def login(self, request: UserLoginRequest) -> tuple[str, UserRecord]:
        return "", self.ensure_default_user()

    def _clean_username(self, username: str) -> str:
        value = username.strip()
        if not value:
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if len(value) > 50:
            raise HTTPException(status_code=400, detail="用户名长度不能超过 50")
        return value


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserRecord:
    return auth_service.get_default_user()


auth_service = AuthService()
