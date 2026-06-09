from fastapi import APIRouter, Depends, Query

from core.schemas import PersonaTurnFeedbackRequest, UserRecord
from services.auth_service import get_current_user
from services.database_service import database_service


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/persona/turn")
def save_persona_turn_feedback(
    request: PersonaTurnFeedbackRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return database_service.save_persona_turn_feedback(
        character_id=request.character_id,
        session_id=request.session_id,
        turn_id=request.turn_id,
        user_message=request.user_message,
        assistant_message=request.assistant_message,
        rating=request.rating,
        issue_tags=request.issue_tags,
        comment=request.comment,
    )


@router.get("/persona/{character_id}")
def persona_feedback_summary(
    character_id: str,
    limit: int = Query(default=30, ge=1, le=100),
    current_user: UserRecord = Depends(get_current_user),
) -> dict:
    return database_service.persona_feedback_summary(character_id=character_id, limit=limit)
