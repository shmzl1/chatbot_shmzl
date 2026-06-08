"""Pydantic models for the characters module."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.schemas import CharacterCard, CharacterListResponse, CharacterSummary


class CharacterDetail(CharacterCard):
    pass


class CharacterCreateRequest(BaseModel):
    character_id: str = Field(..., min_length=1, max_length=80)
    display_name: str = Field(..., min_length=1, max_length=120)
    base_template: str = "default"


class CharacterUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    core_personality: Optional[List[str]] = None
    speaking_style: Optional[List[str]] = None
    relationship_to_user: Optional[str] = None
    forbidden: Optional[List[str]] = None
    reply_patterns: Optional[Dict[str, str]] = None
    style_contract: Optional[Dict[str, Any]] = None
    evaluation_criteria: Optional[List[str]] = None
    bad_examples: Optional[List[Dict[str, Any]]] = None
    revision_notes: Optional[List[Dict[str, Any]]] = None
    lore: Optional[List[Dict[str, Any]]] = None
    dialogues: Optional[List[Dict[str, Any]]] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    voice: Optional[Dict[str, Any]] = None


class CharacterDeleteResponse(BaseModel):
    status: str
    character_id: str
    trash_path: str


class CharacterRestoreResponse(BaseModel):
    status: str
    character: CharacterSummary
    pack_path: str


class CharacterPackValidationResult(BaseModel):
    character_id: str
    display_name: str = ""
    pack_path: str
    character_path: str
    valid: bool = False
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    lore_count: int = 0
    dialogue_count: int = 0
    reaction_count: int = 0
    has_voice_config: bool = False
    has_avatar: bool = False
    is_trashed: bool = False
    backup_exists: bool = False


class CharacterDebugInfo(CharacterPackValidationResult):
    previous_backup_exists: bool = False
    last_revision_note: Optional[Dict[str, Any]] = None
    persona_feedback_count: int = 0
    recent_issue_tag_counts: Dict[str, int] = Field(default_factory=dict)


__all__ = [
    "CharacterCard",
    "CharacterCreateRequest",
    "CharacterDebugInfo",
    "CharacterDeleteResponse",
    "CharacterDetail",
    "CharacterListResponse",
    "CharacterPackValidationResult",
    "CharacterRestoreResponse",
    "CharacterSummary",
    "CharacterUpdateRequest",
]
