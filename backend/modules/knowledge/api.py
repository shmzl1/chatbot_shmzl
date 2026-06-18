from typing import Optional

from fastapi import APIRouter, Depends, Query

from core.config import settings
from core.schemas import DeleteResponse, KnowledgeCreateRequest, KnowledgeListResponse, KnowledgeRecord
from services.auth_service import get_current_user
from services.database_service import database_service


router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=KnowledgeListResponse)
def list_knowledge(
    character_id: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> KnowledgeListResponse:
    return KnowledgeListResponse(
        items=database_service.list_knowledge(
            character_id=character_id,
            source_type=source_type,
            limit=limit,
        )
    )


@router.post("", response_model=KnowledgeRecord)
def create_knowledge(request: KnowledgeCreateRequest) -> KnowledgeRecord:
    return database_service.create_knowledge(
        character_id=request.character_id,
        source_type=request.source_type,
        title=request.title,
        content=request.content,
        tags=request.tags,
    )


@router.post("/import-jsonl")
def import_jsonl(character_id: str = settings.default_character_id) -> dict:
    return database_service.import_jsonl_knowledge(
        data_dir=settings.data_dir,
        character_id=character_id,
    )


@router.delete("/{item_id}", response_model=DeleteResponse)
def delete_knowledge(item_id: int) -> DeleteResponse:
    deleted = database_service.delete_knowledge(item_id)
    return DeleteResponse(status="ok", deleted=deleted)


@router.delete("", response_model=DeleteResponse)
def clear_knowledge(
    character_id: Optional[str] = None,
    source_type: Optional[str] = None,
) -> DeleteResponse:
    deleted = database_service.clear_knowledge(
        character_id=character_id,
        source_type=source_type,
    )
    return DeleteResponse(status="ok", deleted=deleted)
