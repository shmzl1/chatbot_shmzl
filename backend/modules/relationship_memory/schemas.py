"""Schemas for future shared relationship memory events."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RelationshipMemorySourceType(str, Enum):
    CHAT = "chat"
    SCHEDULE = "schedule"
    DIARY = "diary"


class RelationshipMemoryType(str, Enum):
    USER_PREFERENCE = "user_preference"
    HABIT = "habit"
    EMOTIONAL_STATE = "emotional_state"
    LIFE_EVENT = "life_event"
    BOUNDARY = "boundary"
    TASK_PATTERN = "task_pattern"


class RelationshipMemoryEventDraft(BaseModel):
    character_id: str
    source_type: RelationshipMemorySourceType
    source_id: Optional[str] = None
    source_turn_id: Optional[str] = None
    memory_type: RelationshipMemoryType
    content: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(default=5, ge=1, le=10)


class RelationshipMemoryContext(BaseModel):
    character_id: str
    events: List[RelationshipMemoryEventDraft] = Field(default_factory=list)

