"""Filesystem boundary for character packs."""

import re
from pathlib import Path
from typing import List

from fastapi import HTTPException


CHARACTER_FILE = "character.json"
MODULE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = MODULE_DIR / "templates"
PACKS_DIR = MODULE_DIR / "packs"
TRASH_DIR = PACKS_DIR / ".trash"


def normalize_character_id(character_id: str) -> str:
    normalized = str(character_id or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]+", normalized):
        raise HTTPException(
            status_code=400,
            detail="character_id may only contain lowercase letters, numbers, underscore, and hyphen.",
        )
    return normalized


def ensure_roots() -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    TRASH_DIR.mkdir(parents=True, exist_ok=True)


def template_path(base_template: str = "default") -> Path:
    safe_name = str(base_template or "default").strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]+", safe_name):
        raise HTTPException(status_code=400, detail="base_template contains invalid characters.")
    return TEMPLATES_DIR / f"{safe_name}_character.json"


def pack_dir(character_id: str) -> Path:
    return PACKS_DIR / normalize_character_id(character_id)


def trash_pack_dir(character_id: str) -> Path:
    return TRASH_DIR / normalize_character_id(character_id)


def character_path(character_id: str) -> Path:
    return pack_dir(character_id) / CHARACTER_FILE


def backup_path(character_id: str) -> Path:
    return pack_dir(character_id) / "backups" / "character.previous.json"


def active_pack_dirs() -> List[Path]:
    ensure_roots()
    return [
        item
        for item in sorted(PACKS_DIR.iterdir())
        if item.is_dir() and item.name != ".trash" and not item.name.startswith("_")
    ]


def trashed_pack_dirs() -> List[Path]:
    ensure_roots()
    return [item for item in sorted(TRASH_DIR.iterdir()) if item.is_dir()]


def active_pack_exists(character_id: str) -> bool:
    return pack_dir(character_id).exists()


def trashed_pack_exists(character_id: str) -> bool:
    return trash_pack_dir(character_id).exists()


def resolve_pack_relative_path(character_id: str, configured_path: str) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path
    return (pack_dir(character_id) / path).resolve()
