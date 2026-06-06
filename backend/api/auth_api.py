from fastapi import APIRouter, Depends, File, UploadFile

from core.schemas import (
    AuthTokenResponse,
    AvatarUploadResponse,
    UserLoginRequest,
    UserPublic,
    UserRecord,
    UserRegisterRequest,
)
from services.auth_service import auth_service, get_current_user, public_user
from services.avatar_service import avatar_service
from services.database_service import database_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
def register(request: UserRegisterRequest) -> AuthTokenResponse:
    user = auth_service.register(request)
    token, logged_in_user = auth_service.login(
        UserLoginRequest(username_or_email=user.username, password=request.password)
    )
    return AuthTokenResponse(access_token=token, user=public_user(logged_in_user))


@router.post("/login", response_model=AuthTokenResponse)
def login(request: UserLoginRequest) -> AuthTokenResponse:
    token, user = auth_service.login(request)
    return AuthTokenResponse(access_token=token, user=public_user(user))


@router.get("/me", response_model=UserPublic)
def me(current_user: UserRecord = Depends(get_current_user)) -> UserPublic:
    return public_user(current_user)


@router.post("/me/avatar", response_model=AvatarUploadResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
) -> AvatarUploadResponse:
    avatar_url = await avatar_service.save_avatar(
        file=file,
        owner_id=str(current_user.id),
        category="users",
    )
    database_service.update_user_avatar(current_user.id, avatar_url)
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.post("/logout")
def logout() -> dict:
    return {"status": "ok"}
