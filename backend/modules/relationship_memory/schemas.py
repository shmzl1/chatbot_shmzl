"""Schemas for relationship memory events."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RelationshipMemoryCreateRequest(BaseModel):
    character_id: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(default="manual", min_length=1, max_length=50)
    source_id: Optional[str] = None
    source_turn_id: Optional[int] = None
    memory_type: str = Field(default="note", min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=2000)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(default=5, ge=1, le=10)
    is_pinned: bool = False
    is_editable: bool = True
    read_policy: str = Field(default="relevant", pattern="^(always|relevant|never)$")
    status: str = Field(default="active", pattern="^(active|archived|superseded|deleted)$")
    expires_at: Optional[str] = None


class RelationshipMemoryEvent(BaseModel):
    id: int
    character_id: str
    source_type: str
    source_id: Optional[str] = None
    source_turn_id: Optional[int] = None
    memory_type: str
    content: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    importance: int
    is_active: bool
    is_pinned: bool = False
    is_editable: bool = True
    read_policy: str = "relevant"
    status: str = "active"
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    use_count: int = 0
    created_at: str
    updated_at: str


class RelationshipMemoryListResponse(BaseModel):
    events: List[RelationshipMemoryEvent] = Field(default_factory=list)


class RelationshipMemoryDeactivateResponse(BaseModel):
    status: str
    event: Optional[RelationshipMemoryEvent] = None


class RelationshipMemoryContext(BaseModel):
    character_id: str
    events: List[RelationshipMemoryEvent] = Field(default_factory=list)


class RelationshipMemoryDebugResponse(BaseModel):
    character_id: Optional[str] = None
    total_count: int = 0
    active_count: int = 0
    events: List[RelationshipMemoryEvent] = Field(default_factory=list)
