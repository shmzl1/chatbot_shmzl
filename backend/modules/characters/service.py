"""Business service for character packs."""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException

from core.config import settings
from core.schemas import CharacterCard, CharacterSummary
from modules.characters import pack_loader, pack_writer, repository
from modules.characters.schemas import CharacterDebugInfo, CharacterPackValidationResult
from modules.characters.validator import validate_character_pack, validate_pack_dir, validate_payload


class CharacterService:
    def list_characters(self) -> List[CharacterSummary]:
        characters: List[CharacterSummary] = []
        for pack_dir in repository.active_pack_dirs():
            character = pack_loader.load_card(pack_dir.name)
            characters.append(
                CharacterSummary(
                    id=character.id,
                    display_name=character.display_name,
                    avatar_url=character.avatar_url,
                )
            )
        if not characters:
            raise HTTPException(status_code=500, detail=f"No character packs found in {repository.PACKS_DIR}")
        return characters

    def get_character(self, character_id: str) -> CharacterCard:
        return pack_loader.load_card(character_id)

    def create_character(
        self,
        *,
        character_id: str,
        display_name: str,
        base_template: str = "default",
    ) -> CharacterCard:
        pack_writer.create_pack(
            character_id=character_id,
            display_name=display_name,
            base_template=base_template,
        )
        return self.get_character(character_id)

    def update_character(self, character_id: str, updates: Dict[str, Any]) -> CharacterCard:
        character_id = repository.normalize_character_id(character_id)
        if "id" in updates and updates["id"] != character_id:
            raise HTTPException(status_code=400, detail="Character id cannot be changed.")
        updates = {key: value for key, value in updates.items() if key != "id"}
        if not updates:
            return self.get_character(character_id)

        current = pack_loader.load_payload(character_id)
        merged = dict(current)
        merged.update(updates)
        merged["id"] = character_id
        pack_writer.write_payload(character_id=character_id, payload=merged, backup=True)
        return self.get_character(character_id)

    def save_character(self, character: CharacterCard) -> CharacterCard:
        payload = self._model_to_dict(character)
        pack_writer.write_payload(character_id=character.id, payload=payload, backup=True)
        return self.get_character(character.id)

    def delete_character(self, character_id: str) -> Dict[str, Any]:
        trash_path = pack_writer.move_to_trash(character_id)
        return {
            "status": "ok",
            "character_id": repository.normalize_character_id(character_id),
            "trash_path": str(trash_path),
        }

    def restore_character(self, character_id: str) -> Dict[str, Any]:
        pack_path = pack_writer.restore_from_trash(character_id)
        character = self.get_character(character_id)
        return {
            "status": "ok",
            "character": CharacterSummary(
                id=character.id,
                display_name=character.display_name,
                avatar_url=character.avatar_url,
            ).dict(),
            "pack_path": str(pack_path),
        }

    def validate_character_pack(self, character_id: str, *, trashed: bool = False) -> CharacterPackValidationResult:
        return validate_character_pack(character_id, trashed=trashed)

    def validate_pack(self, character_id: str) -> Dict[str, Any]:
        return self.validate_character_pack(character_id).dict()

    def validate_pack_dir(self, pack_dir: Path) -> Dict[str, Any]:
        return validate_pack_dir(pack_dir).dict()

    def validate_all_packs(self) -> List[Dict[str, Any]]:
        return [validate_pack_dir(pack_dir).dict() for pack_dir in repository.active_pack_dirs()]

    def debug_all_characters(self) -> Dict[str, Any]:
        active = [validate_pack_dir(pack_dir).dict() for pack_dir in repository.active_pack_dirs()]
        trashed = [validate_pack_dir(pack_dir, trashed=True).dict() for pack_dir in repository.trashed_pack_dirs()]
        return {
            "active_count": len(active),
            "trashed_count": len(trashed),
            "characters": active,
            "trashed_characters": trashed,
            "packs_dir": str(repository.PACKS_DIR),
            "trash_dir": str(repository.TRASH_DIR),
        }

    def debug_character(self, character_id: str) -> CharacterDebugInfo:
        is_trashed = not repository.active_pack_exists(character_id) and repository.trashed_pack_exists(character_id)
        validation = self.validate_character_pack(character_id, trashed=is_trashed)
        payload: Dict[str, Any] = {}
        if not validation.errors:
            payload = pack_loader.load_payload(character_id, trashed=is_trashed)
        revision_notes = payload.get("revision_notes") if isinstance(payload, dict) else []
        last_revision_note = revision_notes[-1] if isinstance(revision_notes, list) and revision_notes else None
        return CharacterDebugInfo(
            **validation.dict(),
            previous_backup_exists=validation.backup_exists,
            last_revision_note=last_revision_note,
        )

    def get_character_prompt_assets(self, character_id: str) -> Dict[str, Any]:
        character = self.get_character(character_id)
        return {
            "character": character,
            "lore": character.lore,
            "dialogues": character.dialogues,
            "reactions": character.reactions,
        }

    def pack_dir(self, character_id: str) -> Path:
        return repository.pack_dir(character_id)

    def character_path(self, character_id: str) -> Path:
        return repository.character_path(character_id)

    def backup_path(self, character_id: str) -> Path:
        return repository.backup_path(character_id)

    def resolve_pack_relative_path(self, character_id: str, configured_path: str) -> Path:
        return repository.resolve_pack_relative_path(character_id, configured_path)

    def validate_payload(
        self,
        *,
        payload: Dict[str, Any],
        file_path: Path,
        expected_id: str,
        errors: List[str],
    ) -> None:
        validate_payload(
            payload=payload,
            expected_id=expected_id,
            pack_dir=repository.pack_dir(expected_id),
            file_path=file_path,
            errors=errors,
            warnings=[],
        )

    def _validate_payload(
        self,
        *,
        payload: Dict[str, Any],
        file_path: Path,
        expected_id: str,
        errors: List[str],
    ) -> None:
        self.validate_payload(
            payload=payload,
            file_path=file_path,
            expected_id=expected_id,
            errors=errors,
        )

    def _model_to_dict(self, character: CharacterCard) -> Dict[str, Any]:
        if hasattr(character, "model_dump"):
            return character.model_dump()
        return character.dict()


character_service = CharacterService()

__all__ = ["character_service", "CharacterService"]
