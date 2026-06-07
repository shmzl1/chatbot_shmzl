import json
import re
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException
from pydantic import ValidationError

from core.config import settings
from core.schemas import CharacterCard, CharacterSummary


PACK_TEMPLATE_ID = "_template"
CHARACTER_FILE = "character.json"


class CharacterService:
    def __init__(self, character_packs_dir: Path) -> None:
        self.character_packs_dir = character_packs_dir

    def list_characters(self) -> List[CharacterSummary]:
        pack_dirs = self._pack_dirs()
        characters: List[CharacterSummary] = []

        for pack_dir in pack_dirs:
            character = self._load_pack_card(pack_dir)
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
                detail=f"No character packs found in {self.character_packs_dir}",
            )

        return characters

    def get_character(self, character_id: str) -> CharacterCard:
        pack_dir = self._pack_dir(character_id)
        if not pack_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Character pack '{character_id}' not found: {pack_dir}",
            )

        return self._load_pack_card(pack_dir)

    def save_character(self, character: CharacterCard) -> CharacterCard:
        pack_dir = self._pack_dir(character.id)
        pack_dir.mkdir(parents=True, exist_ok=True)
        file_path = pack_dir / CHARACTER_FILE
        payload = self._model_to_dict(character)
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return character

    def validate_all_packs(self) -> List[Dict[str, Any]]:
        if not self.character_packs_dir.exists():
            return [
                {
                    "character_id": "",
                    "display_name": "",
                    "pack_path": str(self.character_packs_dir),
                    "character_path": str(self.character_packs_dir / "*" / CHARACTER_FILE),
                    "lore_count": 0,
                    "dialogue_count": 0,
                    "reaction_count": 0,
                    "has_voice_config": False,
                    "errors": [f"Character packs directory does not exist: {self.character_packs_dir}"],
                }
            ]

        results = []
        for pack_dir in self._pack_dirs(require_root=False):
            results.append(self.validate_pack_dir(pack_dir))
        return results

    def validate_pack(self, character_id: str) -> Dict[str, Any]:
        pack_dir = self._pack_dir(character_id)
        if not pack_dir.exists():
            return self._empty_validation_result(
                character_id=character_id,
                pack_dir=pack_dir,
                errors=[f"Character pack directory does not exist: {pack_dir}"],
            )
        return self.validate_pack_dir(pack_dir)

    def validate_pack_dir(self, pack_dir: Path) -> Dict[str, Any]:
        character_id = pack_dir.name
        file_path = pack_dir / CHARACTER_FILE
        result = self._empty_validation_result(character_id, pack_dir)

        if not file_path.exists():
            result["errors"].append(f"Missing required file: {file_path}")
            return result

        try:
            payload = self._load_json(file_path)
        except HTTPException as exc:
            result["errors"].append(str(exc.detail))
            return result

        if not isinstance(payload, dict):
            result["errors"].append(f"Character file '{file_path}' must contain a JSON object.")
            return result

        result["display_name"] = str(payload.get("display_name") or "")
        result["has_voice_config"] = isinstance(payload.get("voice"), dict)

        self._validate_payload(
            payload=payload,
            file_path=file_path,
            expected_id=character_id,
            errors=result["errors"],
        )
        self._fill_counts(result, payload)
        return result

    def _load_pack_card(self, pack_dir: Path) -> CharacterCard:
        file_path = pack_dir / CHARACTER_FILE
        if not file_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Character pack is missing required file: {file_path}",
            )

        payload = self._load_json(file_path)
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' must contain a JSON object.",
            )

        validation_errors: List[str] = []
        self._validate_payload(
            payload=payload,
            file_path=file_path,
            expected_id=pack_dir.name,
            errors=validation_errors,
        )
        if validation_errors:
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' schema is invalid: {'; '.join(validation_errors)}",
            )

        try:
            return CharacterCard(**payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' schema is invalid: {exc}",
            ) from exc

    def _load_json(self, file_path: Path) -> Any:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Character file '{file_path}' is not valid JSON: {exc}",
            ) from exc

    def _validate_payload(
        self,
        *,
        payload: Dict[str, Any],
        file_path: Path,
        expected_id: str,
        errors: List[str],
    ) -> None:
        if payload.get("id") != expected_id:
            errors.append(f"{file_path}: id must equal directory name '{expected_id}'.")
        if not payload.get("display_name"):
            errors.append(f"{file_path}: display_name is required.")

        for field_name in ("core_personality", "speaking_style", "lore", "dialogues", "reactions"):
            if field_name not in payload:
                errors.append(f"{file_path}: {field_name} is required.")
            elif not isinstance(payload[field_name], list):
                errors.append(f"{file_path}: {field_name} must be an array.")

        for field_name in ("lore", "dialogues", "reactions"):
            values = payload.get(field_name)
            if isinstance(values, list):
                self._validate_collection_ids(file_path, field_name, values, errors)

        voice = payload.get("voice")
        if isinstance(voice, dict):
            ref_audio_path = voice.get("ref_audio_path")
            prompt_text = voice.get("prompt_text")
            if ref_audio_path:
                resolved_ref = self._resolve_pack_path(str(ref_audio_path), file_path.parent)
                if not resolved_ref.exists():
                    errors.append(f"{file_path}: voice.ref_audio_path does not exist: {resolved_ref}")
                if not str(prompt_text or "").strip():
                    errors.append(
                        f"{file_path}: voice.prompt_text cannot be empty when voice.ref_audio_path is configured."
                    )

    def _validate_collection_ids(
        self,
        file_path: Path,
        field_name: str,
        values: List[Any],
        errors: List[str],
    ) -> None:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                errors.append(f"{file_path}: {field_name}[{index}] must be an object.")
                continue
            item_id = item.get("id")
            if not item_id:
                errors.append(f"{file_path}: {field_name}[{index}] is missing id.")
                continue
            item_id = str(item_id)
            if item_id in seen:
                duplicates.add(item_id)
            seen.add(item_id)

        for item_id in sorted(duplicates):
            errors.append(f"{file_path}: duplicate id in {field_name}: {item_id}")

    def _resolve_pack_path(self, configured_path: str, pack_dir: Path) -> Path:
        path = Path(configured_path)
        if path.is_absolute():
            return path

        backend_relative = (settings.data_dir.parent / path).resolve()
        if backend_relative.exists() or configured_path.startswith((".", "data/")):
            return backend_relative

        return (pack_dir / path).resolve()

    def _pack_dirs(self, require_root: bool = True) -> List[Path]:
        if not self.character_packs_dir.exists():
            if require_root:
                raise HTTPException(
                    status_code=500,
                    detail=f"Character packs directory does not exist: {self.character_packs_dir}",
                )
            return []

        return [
            item
            for item in sorted(self.character_packs_dir.iterdir())
            if item.is_dir() and item.name != PACK_TEMPLATE_ID
        ]

    def _pack_dir(self, character_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", character_id):
            raise HTTPException(
                status_code=400,
                detail="Character id may only contain letters, numbers, underscore, and hyphen.",
            )
        return self.character_packs_dir / character_id

    def _empty_validation_result(
        self,
        character_id: str,
        pack_dir: Path,
        errors: List[str] | None = None,
    ) -> Dict[str, Any]:
        return {
            "character_id": character_id,
            "display_name": "",
            "pack_path": str(pack_dir),
            "character_path": str(pack_dir / CHARACTER_FILE),
            "lore_count": 0,
            "dialogue_count": 0,
            "reaction_count": 0,
            "has_voice_config": False,
            "errors": errors or [],
        }

    def _fill_counts(self, result: Dict[str, Any], payload: Dict[str, Any]) -> None:
        result["lore_count"] = self._list_count(payload.get("lore"))
        result["dialogue_count"] = self._list_count(payload.get("dialogues"))
        result["reaction_count"] = self._list_count(payload.get("reactions"))

    def _list_count(self, value: Any) -> int:
        return len(value) if isinstance(value, list) else 0

    def _model_to_dict(self, character: CharacterCard) -> dict:
        if hasattr(character, "model_dump"):
            return character.model_dump()
        return character.dict()


character_service = CharacterService(settings.data_dir / "character_packs")
