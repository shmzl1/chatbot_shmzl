from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    gptsovits: bool
    qdrant: bool
    postgres: bool = False


class CharacterSummary(BaseModel):
    id: str
    display_name: str


class CharacterListResponse(BaseModel):
    characters: List[CharacterSummary]


class VoiceConfig(BaseModel):
    default_emotion: str = "neutral"
    language: str = "zh"
    speed_factor: float = 1.0


class CharacterCard(BaseModel):
    id: str
    display_name: str
    core_personality: List[str] = Field(default_factory=list)
    speaking_style: List[str] = Field(default_factory=list)
    relationship_to_user: str = ""
    forbidden: List[str] = Field(default_factory=list)
    reply_patterns: Dict[str, str] = Field(default_factory=dict)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)


class ChatTextRequest(BaseModel):
    character_id: str = "role01"
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    debug_prompt: bool = False


class ChatRequest(ChatTextRequest):
    voice: bool = False


class CandidateReply(BaseModel):
    reply: str
    emotion: str = "neutral"
    reason: str = ""


class ChatTextResponse(BaseModel):
    session_id: Optional[str] = None
    turn_id: Optional[int] = None
    reply: str
    emotion: str
    candidates: List[CandidateReply] = Field(default_factory=list)
    audio_path: Optional[str] = None
    style_score: Optional[float] = None
    debug: Dict[str, Any] = Field(default_factory=dict)


class VoiceTestRequest(BaseModel):
    character_id: str = "role01"
    text: str = Field(..., min_length=1, max_length=2000)
    emotion: str = "neutral"


class VoiceTestResponse(BaseModel):
    audio_path: str
    public_url: str
    emotion: str


class ChatSessionSummary(BaseModel):
    id: str
    character_id: str
    created_at: str
    updated_at: str
    turn_count: int = 0
    last_user_message: Optional[str] = None
    last_reply: Optional[str] = None


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionSummary]


class ChatTurnRecord(BaseModel):
    id: int
    session_id: str
    character_id: str
    user_message: str
    reply: str
    emotion: str
    candidates: List[CandidateReply] = Field(default_factory=list)
    debug: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ChatTurnListResponse(BaseModel):
    session_id: str
    turns: List[ChatTurnRecord]


class DeleteResponse(BaseModel):
    status: str
    deleted: int = 0


class DatabaseInfoResponse(BaseModel):
    database_backend: str
    database_url: str
    session_count: int
    turn_count: int
    memory_count: int = 0
    knowledge_count: int = 0
    feedback_count: int = 0


class MemoryCreateRequest(BaseModel):
    character_id: str = "role01"
    content: str = Field(..., min_length=1, max_length=2000)
    memory_type: str = "note"
    importance: int = Field(default=5, ge=1, le=10)
    tags: List[str] = Field(default_factory=list)


class MemoryRecord(BaseModel):
    id: int
    character_id: str
    memory_type: str
    content: str
    importance: int
    tags: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    last_used_at: Optional[str] = None


class MemoryListResponse(BaseModel):
    memories: List[MemoryRecord]


class KnowledgeCreateRequest(BaseModel):
    character_id: str = "role01"
    source_type: str = Field(default="lore", pattern="^(lore|dialogue|reaction)$")
    title: str = Field(default="", max_length=200)
    content: str = Field(..., min_length=1, max_length=4000)
    tags: List[str] = Field(default_factory=list)


class KnowledgeRecord(BaseModel):
    id: int
    character_id: str
    source_type: str
    title: str = ""
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class KnowledgeListResponse(BaseModel):
    items: List[KnowledgeRecord]


class TurnFeedbackRequest(BaseModel):
    score: int = Field(..., ge=1, le=10)
    note: str = Field(default="", max_length=2000)


class TurnFeedbackResponse(BaseModel):
    id: int
    turn_id: int
    score: int
    note: str = ""
    created_at: str
