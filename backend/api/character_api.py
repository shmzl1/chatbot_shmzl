from fastapi import APIRouter

from core.schemas import CharacterCard, CharacterListResponse
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
