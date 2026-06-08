"""Validation for character packs."""

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from core.schemas import CharacterCard
from modules.characters import repository
from modules.characters.schemas import CharacterPackValidationResult


def validate_character_pack(character_id: str, *, trashed: bool = False) -> CharacterPackValidationResult:
    pack_dir = repository.trash_pack_dir(character_id) if trashed else repository.pack_dir(character_id)
    return validate_pack_dir(pack_dir, trashed=trashed)


def validate_pack_dir(pack_dir: Path, *, trashed: bool = False) -> CharacterPackValidationResult:
    character_id = pack_dir.name
    file_path = pack_dir / repository.CHARACTER_FILE
    result = CharacterPackValidationResult(
        character_id=character_id,
        pack_path=str(pack_dir),
        character_path=str(file_path),
        is_trashed=trashed,
        backup_exists=(pack_dir / "backups" / "character.previous.json").exists(),
    )

    if not pack_dir.exists():
        result.errors.append(f"Character pack directory does not exist: {pack_dir}")
        return _finalize(result)

    if not file_path.exists():
        result.errors.append(f"Missing required file: {file_path}")
        return _finalize(result)

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"Character file '{file_path}' is not valid JSON: {exc}")
        return _finalize(result)

    if not isinstance(payload, dict):
        result.errors.append(f"Character file '{file_path}' must contain a JSON object.")
        return _finalize(result)

    result.display_name = str(payload.get("display_name") or "")
    result.has_voice_config = isinstance(payload.get("voice"), dict)
    result.has_avatar = isinstance(payload.get("avatar_url"), str) and bool(payload.get("avatar_url"))
    result.lore_count = _list_count(payload.get("lore"))
    result.dialogue_count = _list_count(payload.get("dialogues"))
    result.reaction_count = _list_count(payload.get("reactions"))

    validate_payload(
        payload=payload,
        expected_id=character_id,
        pack_dir=pack_dir,
        file_path=file_path,
        errors=result.errors,
        warnings=result.warnings,
    )
    try:
        CharacterCard(**payload)
    except ValidationError as exc:
        result.errors.append(f"{file_path}: schema is invalid: {exc}")

    return _finalize(result)


def validate_payload(
    *,
    payload: Dict[str, Any],
    expected_id: str,
    pack_dir: Path,
    file_path: Path,
    errors: List[str],
    warnings: List[str],
) -> None:
    if payload.get("id") != expected_id:
        errors.append(f"{file_path}: id must equal directory name '{expected_id}'.")

    if not payload.get("display_name"):
        errors.append(f"{file_path}: display_name is required.")

    avatar_url = payload.get("avatar_url")
    if avatar_url is not None and not isinstance(avatar_url, str):
        errors.append(f"{file_path}: avatar_url must be a string or null.")

    for field_name in ("core_personality", "speaking_style", "lore", "dialogues", "reactions"):
        if field_name not in payload:
            errors.append(f"{file_path}: {field_name} is required.")
        elif not isinstance(payload[field_name], list):
            errors.append(f"{file_path}: {field_name} must be an array.")

    for field_name in ("lore", "dialogues", "reactions"):
        values = payload.get(field_name)
        if isinstance(values, list):
            _validate_collection_ids(file_path, field_name, values, errors)

    _validate_style_contract(file_path, payload.get("style_contract"), errors)

    for field_name in ("evaluation_criteria", "bad_examples", "revision_notes"):
        if field_name not in payload:
            errors.append(f"{file_path}: {field_name} is required.")
        elif not isinstance(payload[field_name], list):
            errors.append(f"{file_path}: {field_name} must be an array.")

    _validate_voice(file_path, pack_dir, payload.get("voice"), errors, warnings)


def _validate_style_contract(file_path: Path, value: Any, errors: List[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{file_path}: style_contract must be an object.")
        return
    for field_name in ("must", "should", "avoid", "hard_bans"):
        if field_name not in value:
            errors.append(f"{file_path}: style_contract.{field_name} is required.")
        elif not isinstance(value[field_name], list):
            errors.append(f"{file_path}: style_contract.{field_name} must be an array.")


def _validate_voice(
    file_path: Path,
    pack_dir: Path,
    value: Any,
    errors: List[str],
    warnings: List[str],
) -> None:
    if value is None:
        warnings.append(f"{file_path}: voice config is missing.")
        return
    if not isinstance(value, dict):
        errors.append(f"{file_path}: voice must be an object.")
        return

    if "speed_factor" in value and not isinstance(value["speed_factor"], (int, float)):
        errors.append(f"{file_path}: voice.speed_factor must be a number.")

    ref_audio_path = value.get("ref_audio_path")
    prompt_text = value.get("prompt_text")
    if ref_audio_path:
        resolved_ref = _resolve_pack_path(str(ref_audio_path), pack_dir)
        if not resolved_ref.exists():
            errors.append(f"{file_path}: voice.ref_audio_path does not exist: {resolved_ref}")
        if not str(prompt_text or "").strip():
            errors.append(f"{file_path}: voice.prompt_text cannot be empty when voice.ref_audio_path is configured.")


def _validate_collection_ids(
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


def _resolve_pack_path(configured_path: str, pack_dir: Path) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path
    return (pack_dir / path).resolve()


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _finalize(result: CharacterPackValidationResult) -> CharacterPackValidationResult:
    result.valid = not result.errors
    return result
