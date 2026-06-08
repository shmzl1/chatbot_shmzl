"""Compatibility exports for the characters module.

New character-pack code lives under `modules.characters`. This module remains
so older imports keep working while the backend migrates feature by feature.
"""

from modules.characters.repository import CHARACTER_FILE
from modules.characters.service import CharacterService, character_service

PACK_TEMPLATE_ID = "default"

__all__ = ["CHARACTER_FILE", "PACK_TEMPLATE_ID", "CharacterService", "character_service"]
