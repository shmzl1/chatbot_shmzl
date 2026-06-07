from fastapi import APIRouter, Depends, File, UploadFile

from core.schemas import AvatarUploadResponse, CharacterCard, CharacterListResponse, UserRecord
from core.schemas import PersonaReviewApplyRequest, PersonaReviewSummarizeRequest
from services.auth_service import get_current_user
from services.avatar_service import avatar_service
from services.character_service import character_service
from services.database_service import database_service
from services.persona_review_service import persona_review_service


router = APIRouter(tags=["characters"])


@router.get("/characters", response_model=CharacterListResponse)
def list_characters() -> CharacterListResponse:
    avatars = database_service.get_character_avatar_map()
    characters = []
    for character in character_service.list_characters():
        avatar_url = avatars.get(character.id, character.avatar_url)
        characters.append(character.copy(update={"avatar_url": avatar_url}))
    return CharacterListResponse(characters=characters)


@router.get("/characters/{character_id}", response_model=CharacterCard)
def get_character(character_id: str) -> CharacterCard:
    character = character_service.get_character(character_id)
    avatar_url = database_service.get_character_avatar(character_id)
    if avatar_url:
        character = character.copy(update={"avatar_url": avatar_url})
    return character


@router.put("/characters/{character_id}", response_model=CharacterCard)
def update_character(
    character_id: str,
    character: CharacterCard,
    current_user: UserRecord = Depends(get_current_user),
) -> CharacterCard:
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
    database_service.upsert_character_avatar(character.id, avatar_url)
    updated = character.copy(update={"avatar_url": avatar_url})
    character_service.save_character(updated)
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.post("/characters/{character_id}/persona-review/summarize")
def summarize_persona_review(
    character_id: str,
    request: PersonaReviewSummarizeRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return persona_review_service.summarize(character_id=character_id, limit=request.limit)


@router.post("/characters/{character_id}/persona-review/apply")
def apply_persona_review(
    character_id: str,
    request: PersonaReviewApplyRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return persona_review_service.apply(
        character_id=character_id,
        preview_character_json=request.preview_character_json,
        review_summary=request.review_summary,
    )


@router.post("/characters/{character_id}/persona-review/rollback")
def rollback_persona_review(
    character_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return persona_review_service.rollback(character_id)
