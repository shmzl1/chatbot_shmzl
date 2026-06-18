from fastapi import APIRouter, Depends, File, UploadFile

from core.schemas import (
    AuthStatusResponse,
    AvatarUploadResponse,
    UserProfileUpdateRequest,
    UserPublic,
    UserRecord,
)
from services.auth_service import auth_service, get_current_user, public_user
from services.avatar_service import avatar_service
from services.database_service import database_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusResponse)
def status() -> AuthStatusResponse:
    auth_service.ensure_default_user()
    return AuthStatusResponse(has_user=True)


@router.get("/me", response_model=UserPublic)
def me(current_user: UserRecord = Depends(get_current_user)) -> UserPublic:
    return public_user(current_user)


@router.put("/me", response_model=UserPublic)
def update_me(request: UserProfileUpdateRequest) -> UserPublic:
    return public_user(auth_service.update_default_user_profile(username=request.username))


@router.post("/me/avatar", response_model=AvatarUploadResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
) -> AvatarUploadResponse:
    avatar_url = await avatar_service.save_avatar(
        file=file,
        owner_id="user_avatar",
        category="user",
    )
    database_service.update_user_avatar(current_user.id, avatar_url)
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.post("/logout")
def logout() -> dict:
    return {"status": "ok"}
