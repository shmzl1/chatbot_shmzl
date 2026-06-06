from typing import Optional

from fastapi import APIRouter, Query

from core.schemas import DeleteResponse, MemoryCreateRequest, MemoryListResponse, MemoryRecord
from services.database_service import database_service


router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=MemoryListResponse)
def list_memories(
    character_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> MemoryListResponse:
    return MemoryListResponse(
        memories=database_service.list_memories(
            character_id=character_id,
            limit=limit,
        )
    )


@router.post("", response_model=MemoryRecord)
def create_memory(request: MemoryCreateRequest) -> MemoryRecord:
    return database_service.create_memory(
        character_id=request.character_id,
        content=request.content,
        memory_type=request.memory_type,
        importance=request.importance,
        tags=request.tags,
    )


@router.delete("/{memory_id}", response_model=DeleteResponse)
def delete_memory(memory_id: int) -> DeleteResponse:
    deleted = database_service.delete_memory(memory_id)
    return DeleteResponse(status="ok", deleted=deleted)


@router.delete("", response_model=DeleteResponse)
def clear_memories(character_id: Optional[str] = None) -> DeleteResponse:
    deleted = database_service.clear_memories(character_id=character_id)
    return DeleteResponse(status="ok", deleted=deleted)
