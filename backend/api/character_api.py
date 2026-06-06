from fastapi import APIRouter, Depends, File, UploadFile

from core.schemas import AvatarUploadResponse, CharacterCard, CharacterListResponse, UserRecord
from services.auth_service import get_current_user
from services.avatar_service import avatar_service
from services.character_service import character_service


router = APIRouter(tags=["characters"])


@router.get("/characters", response_model=CharacterListResponse)
def list_characters() -> CharacterListResponse:
    return CharacterListResponse(characters=character_service.list_characters())


@router.get("/characters/{character_id}", response_model=CharacterCard)
def get_character(character_id: str) -> CharacterCard:
    return character_service.get_character(character_id)


@router.put("/characters/{character_id}", response_model=CharacterCard)
def update_character(character_id: str, character: CharacterCard) -> CharacterCard:
    if character.id != character_id:
        character = character.copy(update={"id": character_id})
    return character_service.save_character(character)


@router.post("/characters/{character_id}/avatar", response_model=AvatarUploadResponse)
async def upload_character_avatar(
    character_id: str,
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
) -> AvatarUploadResponse:
    character = character_service.get_character(character_id)
    avatar_url = await avatar_service.save_avatar(
        file=file,
        owner_id=character.id,
        category="characters",
    )
    updated = character.copy(update={"avatar_url": avatar_url})
    character_service.save_character(updated)
    return AvatarUploadResponse(avatar_url=avatar_url)
