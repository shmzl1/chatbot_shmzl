"""Character management API."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, File, UploadFile

from core.schemas import (
    AvatarUploadResponse,
    PersonaReviewApplyRequest,
    PersonaReviewChatRequest,
    PersonaReviewChatResponse,
    PersonaReviewFinalizeRequest,
    PersonaReviewFinalizeResponse,
    PersonaReviewSummarizeRequest,
    UserRecord,
)
from modules.characters.schemas import (
    CharacterCard,
    CharacterCreateRequest,
    CharacterDeleteResponse,
    CharacterDetail,
    CharacterListResponse,
    CharacterPackValidationResult,
    CharacterRestoreResponse,
    CharacterUpdateRequest,
)
from modules.characters.service import character_service
from services.auth_service import get_current_user
from services.avatar_service import avatar_service
from services.database_service import database_service
from modules.persona_review.service import persona_review_service


router = APIRouter(tags=["characters"])


@router.get("/characters", response_model=CharacterListResponse)
def list_characters() -> CharacterListResponse:
    avatars = database_service.get_character_avatar_map()
    characters = []
    for character in character_service.list_characters():
        avatar_url = avatars.get(character.id, character.avatar_url)
        characters.append(character.copy(update={"avatar_url": avatar_url}))
    return CharacterListResponse(characters=characters)


@router.post("/characters", response_model=CharacterDetail)
def create_character(
    request: CharacterCreateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> CharacterCard:
    return character_service.create_character(
        character_id=request.character_id,
        display_name=request.display_name,
        base_template=request.base_template,
    )


@router.get("/characters/{character_id}", response_model=CharacterDetail)
def get_character(character_id: str) -> CharacterCard:
    character = character_service.get_character(character_id)
    avatar_url = database_service.get_character_avatar(character_id)
    if avatar_url:
        character = character.copy(update={"avatar_url": avatar_url})
    return character


@router.patch("/characters/{character_id}", response_model=CharacterDetail)
def patch_character(
    character_id: str,
    request: CharacterUpdateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> CharacterCard:
    updates = _model_to_update_dict(request)
    return character_service.update_character(character_id, updates)


@router.put("/characters/{character_id}", response_model=CharacterDetail)
def update_character(
    character_id: str,
    character: CharacterCard,
    current_user: UserRecord = Depends(get_current_user),
) -> CharacterCard:
    payload = _model_to_dict(character)
    payload["id"] = character_id
    return character_service.update_character(character_id, payload)


@router.delete("/characters/{character_id}", response_model=CharacterDeleteResponse)
def delete_character(
    character_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> Dict[str, Any]:
    return character_service.delete_character(character_id)


@router.post("/characters/{character_id}/restore", response_model=CharacterRestoreResponse)
def restore_character(
    character_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> Dict[str, Any]:
    return character_service.restore_character(character_id)


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
    character_service.update_character(character.id, {"avatar_url": avatar_url})
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.get("/characters/{character_id}/validate", response_model=CharacterPackValidationResult)
def validate_character(character_id: str) -> CharacterPackValidationResult:
    return character_service.validate_character_pack(character_id)


@router.post("/characters/{character_id}/persona-review/summarize")
def summarize_persona_review(
    character_id: str,
    request: PersonaReviewSummarizeRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return persona_review_service.summarize(character_id=character_id, limit=request.limit)


@router.post(
    "/characters/{character_id}/persona-review/chat",
    response_model=PersonaReviewChatResponse,
)
def chat_persona_review(
    character_id: str,
    request: PersonaReviewChatRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> PersonaReviewChatResponse:
    return persona_review_service.chat(
        character_id=character_id,
        selected_turns=request.selected_turns,
        message=request.message,
        history=request.history,
    )


@router.post(
    "/characters/{character_id}/persona-review/finalize",
    response_model=PersonaReviewFinalizeResponse,
)
def finalize_persona_review(
    character_id: str,
    request: PersonaReviewFinalizeRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> PersonaReviewFinalizeResponse:
    return persona_review_service.finalize(
        character_id=character_id,
        selected_turns=request.selected_turns,
        history=request.history,
        limit=request.limit,
    )


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


def _model_to_update_dict(model: CharacterUpdateRequest) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _model_to_dict(model: CharacterCard) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


__all__ = ["router"]
