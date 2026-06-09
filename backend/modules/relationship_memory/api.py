from typing import Optional

from fastapi import APIRouter, Depends, Query

from modules.relationship_memory.schemas import (
    RelationshipMemoryCreateRequest,
    RelationshipMemoryDeactivateResponse,
    RelationshipMemoryDebugResponse,
    RelationshipMemoryEvent,
    RelationshipMemoryListResponse,
)
from modules.relationship_memory.service import relationship_memory_service
from services.auth_service import get_current_user


router = APIRouter(
    prefix="/relationship-memory",
    tags=["relationship_memory"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=RelationshipMemoryEvent)
def create_relationship_memory(request: RelationshipMemoryCreateRequest) -> RelationshipMemoryEvent:
    return relationship_memory_service.create(request)


@router.get("", response_model=RelationshipMemoryListResponse)
def list_relationship_memory(
    character_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> RelationshipMemoryListResponse:
    return RelationshipMemoryListResponse(
        events=relationship_memory_service.list_active(
            character_id=character_id,
            limit=limit,
        )
    )


@router.post("/{event_id}/deactivate", response_model=RelationshipMemoryDeactivateResponse)
def deactivate_relationship_memory(event_id: int) -> RelationshipMemoryDeactivateResponse:
    return RelationshipMemoryDeactivateResponse(
        status="ok",
        event=relationship_memory_service.deactivate(event_id),
    )


@router.get("/debug", response_model=RelationshipMemoryDebugResponse)
def debug_relationship_memory(
    character_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> RelationshipMemoryDebugResponse:
    return RelationshipMemoryDebugResponse(
        **relationship_memory_service.debug(
            character_id=character_id,
            limit=limit,
        )
    )
