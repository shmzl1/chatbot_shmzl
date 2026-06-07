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
    avatar_url: Optional[str] = None


class CharacterListResponse(BaseModel):
    characters: List[CharacterSummary]


class VoiceConfig(BaseModel):
    default_emotion: str = "neutral"
    language: str = "zh"
    text_lang: str = "zh"
    prompt_lang: str = "zh"
    speed_factor: float = 1.0
    gptsovits_base_url: Optional[str] = None
    ref_audio_path: Optional[str] = None
    prompt_text: str = ""


class StyleContract(BaseModel):
    must: List[str] = Field(default_factory=list)
    should: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)
    hard_bans: List[str] = Field(default_factory=list)


class CharacterCard(BaseModel):
    id: str
    display_name: str
    avatar_url: Optional[str] = None
    core_personality: List[str]
    speaking_style: List[str]
    relationship_to_user: str = ""
    forbidden: List[str] = Field(default_factory=list)
    reply_patterns: Dict[str, str] = Field(default_factory=dict)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    lore: List[Dict[str, Any]]
    dialogues: List[Dict[str, Any]]
    reactions: List[Dict[str, Any]]
    style_contract: StyleContract = Field(default_factory=StyleContract)
    evaluation_criteria: List[str] = Field(default_factory=list)
    bad_examples: List[Dict[str, Any]] = Field(default_factory=list)
    revision_notes: List[Dict[str, Any]] = Field(default_factory=list)


class PersonaTurnFeedbackRequest(BaseModel):
    character_id: str
    session_id: Optional[str] = None
    turn_id: Optional[int] = None
    user_message: str = Field(..., min_length=1, max_length=4000)
    assistant_message: str = Field(..., min_length=1, max_length=4000)
    rating: str = Field(..., pattern="^(good|bad|neutral)$")
    issue_tags: List[str] = Field(default_factory=list)
    comment: str = Field(default="", max_length=2000)


class PersonaReviewSummarizeRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)


class PersonaReviewSelectedTurn(BaseModel):
    turn_id: Optional[int] = None
    session_id: Optional[str] = None
    user_message: str = Field(..., min_length=1, max_length=4000)
    assistant_message: str = Field(..., min_length=1, max_length=4000)


class PersonaReviewHistoryMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=8000)


class PersonaReviewChatRequest(BaseModel):
    selected_turns: List[PersonaReviewSelectedTurn] = Field(default_factory=list)
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[PersonaReviewHistoryMessage] = Field(default_factory=list)


class PersonaReviewFinalizeRequest(BaseModel):
    selected_turns: List[PersonaReviewSelectedTurn] = Field(default_factory=list)
    history: List[PersonaReviewHistoryMessage] = Field(default_factory=list)
    limit: int = Field(default=30, ge=1, le=100)


class PersonaReviewApplyRequest(BaseModel):
    preview_character_json: Dict[str, Any]
    review_summary: Dict[str, Any] = Field(default_factory=dict)


class PersonaReviewRollbackResponse(BaseModel):
    status: str
    character: CharacterSummary
    restored_from: str


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
    persona_feedback_count: int = 0


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


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str


class UserSetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str


class AuthStatusResponse(BaseModel):
    has_user: bool


class UserRecord(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    password_hash: str
    avatar_url: Optional[str] = None
    created_at: str
    updated_at: str


class UserPublic(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class AvatarUploadResponse(BaseModel):
    avatar_url: str
