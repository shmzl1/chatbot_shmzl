import json
import re
from pathlib import Path
from typing import List

from fastapi import HTTPException
from pydantic import ValidationError

from core.config import settings
from core.schemas import CharacterCard, CharacterSummary


class CharacterService:
    def __init__(self, characters_dir: Path) -> None:
        self.characters_dir = characters_dir

    def list_characters(self) -> List[CharacterSummary]:
        if not self.characters_dir.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Characters directory does not exist: {self.characters_dir}",
            )

        characters: List[CharacterSummary] = []
        for file_path in sorted(self.characters_dir.glob("*.json")):
            character = self._load_card(file_path)
            characters.append(
                CharacterSummary(
                    id=character.id,
                    display_name=character.display_name,
                    avatar_url=character.avatar_url,
                )
            )

        if not characters:
            raise HTTPException(
                status_code=500,
                detail=f"No character JSON files found in {self.characters_dir}",
            )

        return characters

    def get_character(self, character_id: str) -> CharacterCard:
        file_path = self._character_path(character_id)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Character '{character_id}' not found: {file_path}",
            )

        return self._load_card(file_path)

    def save_character(self, character: CharacterCard) -> CharacterCard:
        file_path = self._character_path(character.id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._model_to_dict(character)
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return character

    def _load_card(self, file_path: Path) -> CharacterCard:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            return CharacterCard(**payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' is not valid JSON: {exc}",
            ) from exc
        except ValidationError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' schema is invalid: {exc}",
            ) from exc

    def _character_path(self, character_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", character_id):
            raise HTTPException(
                status_code=400,
                detail="Character id may only contain letters, numbers, underscore, and hyphen.",
            )
        return self.characters_dir / f"{character_id}.json"

    def _model_to_dict(self, character: CharacterCard) -> dict:
        if hasattr(character, "model_dump"):
            return character.model_dump()
        return character.dict()


character_service = CharacterService(settings.data_dir / "characters")
