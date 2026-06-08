"""Write character packs safely."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException
from pydantic import ValidationError

from core.config import settings
from core.schemas import CharacterCard
from modules.characters import pack_loader, repository
from modules.characters.validator import validate_pack_dir, validate_payload


def create_pack(*, character_id: str, display_name: str, base_template: str = "default") -> Dict[str, Any]:
    character_id = repository.normalize_character_id(character_id)
    display_name = str(display_name or "").strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name cannot be empty.")

    pack_dir = repository.pack_dir(character_id)
    trash_dir = repository.trash_pack_dir(character_id)
    template_path = repository.template_path(base_template)

    if pack_dir.exists():
        raise HTTPException(status_code=409, detail=f"Character pack already exists: {pack_dir}")
    if trash_dir.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Character pack exists in trash: {trash_dir}. Restore or clear trash before creating it again.",
        )
    if not template_path.exists():
        raise HTTPException(status_code=500, detail=f"Character template does not exist: {template_path}")

    template = pack_loader.load_payload_from_path(template_path)
    template["id"] = character_id
    template["display_name"] = display_name

    pack_dir.mkdir(parents=True, exist_ok=False)
    (pack_dir / "voice_refs" / "neutral").mkdir(parents=True, exist_ok=True)
    (pack_dir / "backups").mkdir(parents=True, exist_ok=True)
    _touch_gitkeep(pack_dir / "voice_refs" / "neutral" / ".gitkeep")
    _touch_gitkeep(pack_dir / "backups" / ".gitkeep")

    try:
        write_payload(character_id=character_id, payload=template, backup=False)
    except Exception:
        shutil.rmtree(pack_dir, ignore_errors=True)
        raise

    return template


def write_payload(*, character_id: str, payload: Dict[str, Any], backup: bool = True) -> Dict[str, Any]:
    character_id = repository.normalize_character_id(character_id)
    pack_dir = repository.pack_dir(character_id)
    file_path = repository.character_path(character_id)
    temp_path = file_path.with_suffix(".tmp.json")
    backup_file = repository.backup_path(character_id)

    if payload.get("id") != character_id:
        raise HTTPException(status_code=400, detail="Character payload id cannot be changed.")

    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "backups").mkdir(parents=True, exist_ok=True)

    try:
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp_payload = pack_loader.load_payload_from_path(temp_path)
        temp_errors: list[str] = []
        temp_warnings: list[str] = []
        validate_payload(
            payload=temp_payload,
            expected_id=character_id,
            pack_dir=pack_dir,
            file_path=temp_path,
            errors=temp_errors,
            warnings=temp_warnings,
        )
        try:
            CharacterCard(**temp_payload)
        except ValidationError as exc:
            temp_errors.append(f"{temp_path}: schema is invalid: {exc}")
        if temp_errors:
            raise HTTPException(
                status_code=500,
                detail=f"Character preview '{temp_path}' is invalid: {'; '.join(temp_errors)}",
            )
        if backup and file_path.exists():
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_file)
        os.replace(temp_path, file_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    final_validation = validate_pack_dir(pack_dir)
    if final_validation.errors:
        raise HTTPException(
            status_code=500,
            detail=f"Character pack '{character_id}' is invalid after write: {'; '.join(final_validation.errors)}",
        )
    return payload


def move_to_trash(character_id: str) -> Path:
    character_id = repository.normalize_character_id(character_id)
    if character_id == str(settings.default_character_id).lower():
        raise HTTPException(status_code=400, detail=f"Cannot delete default character '{character_id}'.")

    pack_dir = repository.pack_dir(character_id)
    trash_dir = repository.trash_pack_dir(character_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail=f"Character pack '{character_id}' not found: {pack_dir}")
    if trash_dir.exists():
        raise HTTPException(status_code=409, detail=f"Trash already contains character '{character_id}': {trash_dir}")

    repository.TRASH_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pack_dir), str(trash_dir))
    return trash_dir


def restore_from_trash(character_id: str) -> Path:
    character_id = repository.normalize_character_id(character_id)
    pack_dir = repository.pack_dir(character_id)
    trash_dir = repository.trash_pack_dir(character_id)
    if pack_dir.exists():
        raise HTTPException(status_code=409, detail=f"Active character already exists: {pack_dir}")
    if not trash_dir.exists():
        raise HTTPException(status_code=404, detail=f"Trashed character not found: {trash_dir}")

    validation = validate_pack_dir(trash_dir, trashed=True)
    if validation.errors:
        raise HTTPException(
            status_code=500,
            detail=f"Trashed character pack '{character_id}' is invalid: {'; '.join(validation.errors)}",
        )

    shutil.move(str(trash_dir), str(pack_dir))
    final_validation = validate_pack_dir(pack_dir)
    if final_validation.errors:
        raise HTTPException(
            status_code=500,
            detail=f"Restored character pack '{character_id}' is invalid: {'; '.join(final_validation.errors)}",
        )
    return pack_dir


def restore_previous_backup(character_id: str) -> Path:
    character_id = repository.normalize_character_id(character_id)
    pack_dir = repository.pack_dir(character_id)
    file_path = repository.character_path(character_id)
    backup_file = repository.backup_path(character_id)
    temp_path = file_path.with_suffix(".rollback.tmp.json")

    if not backup_file.exists():
        raise HTTPException(status_code=404, detail=f"Previous character backup does not exist: {backup_file}")

    payload = pack_loader.load_payload_from_path(backup_file)
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        temp_payload = pack_loader.load_payload_from_path(temp_path)
        temp_errors: list[str] = []
        temp_warnings: list[str] = []
        validate_payload(
            payload=temp_payload,
            expected_id=character_id,
            pack_dir=pack_dir,
            file_path=temp_path,
            errors=temp_errors,
            warnings=temp_warnings,
        )
        try:
            CharacterCard(**temp_payload)
        except ValidationError as exc:
            temp_errors.append(f"{temp_path}: schema is invalid: {exc}")
        if temp_errors:
            raise HTTPException(
                status_code=500,
                detail=f"Character rollback payload '{temp_path}' is invalid: {'; '.join(temp_errors)}",
            )
        os.replace(temp_path, file_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    final_validation = validate_pack_dir(pack_dir)
    if final_validation.errors:
        raise HTTPException(
            status_code=500,
            detail=f"Character pack '{character_id}' is invalid after rollback: {'; '.join(final_validation.errors)}",
        )
    return backup_file


def _touch_gitkeep(path: Path) -> None:
    if not path.exists():
        path.write_text("", encoding="utf-8")
