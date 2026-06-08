from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from core.schemas import (
    ChatSessionListResponse,
    ChatTurnListResponse,
    DatabaseInfoResponse,
    DeleteResponse,
    TurnFeedbackRequest,
    TurnFeedbackResponse,
    UserRecord,
)
from services.auth_service import get_current_user
from modules.characters.service import character_service
from services.database_service import database_service
from services.persona_review_service import persona_review_service


router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/database", response_model=DatabaseInfoResponse)
def database_info() -> DatabaseInfoResponse:
    return DatabaseInfoResponse(**database_service.info())


@router.get("/export")
def export_debug_data() -> JSONResponse:
    return JSONResponse(content=database_service.export_data())


@router.get("/characters")
def debug_characters() -> JSONResponse:
    return JSONResponse(content=character_service.debug_all_characters())


@router.get("/characters/{character_id}")
def debug_character(character_id: str) -> JSONResponse:
    return JSONResponse(content=persona_review_service.debug(character_id))


@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: UserRecord = Depends(get_current_user),
) -> ChatSessionListResponse:
    return ChatSessionListResponse(sessions=database_service.list_sessions(limit=limit))


@router.get("/sessions/{session_id}/turns", response_model=ChatTurnListResponse)
def list_turns(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatTurnListResponse:
    return ChatTurnListResponse(
        session_id=session_id,
        turns=database_service.list_turns(session_id),
    )


@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
def delete_session(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> DeleteResponse:
    deleted = database_service.delete_session(session_id)
    return DeleteResponse(status="ok", deleted=deleted)


@router.delete("/sessions", response_model=DeleteResponse)
def clear_sessions(current_user: UserRecord = Depends(get_current_user)) -> DeleteResponse:
    deleted = database_service.clear_sessions()
    return DeleteResponse(status="ok", deleted=deleted)


@router.post("/turns/{turn_id}/feedback", response_model=TurnFeedbackResponse)
def save_feedback(
    turn_id: int,
    request: TurnFeedbackRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> TurnFeedbackResponse:
    return TurnFeedbackResponse(
        **database_service.save_feedback(
            turn_id=turn_id,
            score=request.score,
            note=request.note,
        )
    )
