"""Read character packs from the characters module."""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException
from pydantic import ValidationError

from core.schemas import CharacterCard
from modules.characters import repository
from modules.characters.validator import validate_pack_dir


def load_payload(character_id: str, *, trashed: bool = False) -> Dict[str, Any]:
    pack_dir = repository.trash_pack_dir(character_id) if trashed else repository.pack_dir(character_id)
    file_path = pack_dir / repository.CHARACTER_FILE
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail=f"Character pack '{character_id}' not found: {pack_dir}")
    if not file_path.exists():
        raise HTTPException(status_code=500, detail=f"Character pack is missing required file: {file_path}")

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Character file '{file_path}' is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail=f"Character file '{file_path}' must contain a JSON object.")
    return payload


def load_card(character_id: str, *, trashed: bool = False) -> CharacterCard:
    pack_dir = repository.trash_pack_dir(character_id) if trashed else repository.pack_dir(character_id)
    validation = validate_pack_dir(pack_dir, trashed=trashed)
    if validation.errors:
        raise HTTPException(
            status_code=500 if pack_dir.exists() else 404,
            detail=f"Character pack '{character_id}' is invalid: {'; '.join(validation.errors)}",
        )
    payload = load_payload(character_id, trashed=trashed)
    try:
        return CharacterCard(**payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Character file '{pack_dir / repository.CHARACTER_FILE}' schema is invalid: {exc}",
        ) from exc


def load_payload_from_path(file_path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Character JSON is invalid at {file_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail=f"Character JSON root must be an object: {file_path}")
    return payload
