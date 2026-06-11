"""API routes for the local diary module."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.schemas import DeleteResponse, UserRecord
from modules.diary.schemas import (
    DiaryEntryCreateRequest,
    DiaryEntryDetail,
    DiaryEntryListResponse,
    DiaryEntryUpdateRequest,
    DiaryImageUploadResponse,
)
from modules.diary.service import diary_service
from services.auth_service import get_current_user


router = APIRouter(prefix="/diary", tags=["diary"])


@router.get("/entries", response_model=DiaryEntryListResponse)
def list_entries(
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    mood: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserRecord = Depends(get_current_user),
) -> DiaryEntryListResponse:
    entries = diary_service.list_entries(
        user_id=current_user.id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        mood=mood,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    return DiaryEntryListResponse(entries=entries)


@router.post("/entries", response_model=DiaryEntryDetail)
def create_entry(
    request: DiaryEntryCreateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> DiaryEntryDetail:
    return diary_service.create_entry(user_id=current_user.id, request=request)


@router.get("/entries/{entry_id}", response_model=DiaryEntryDetail)
def get_entry(
    entry_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> DiaryEntryDetail:
    return diary_service.get_entry(user_id=current_user.id, entry_id=entry_id)


@router.put("/entries/{entry_id}", response_model=DiaryEntryDetail)
def update_entry(
    entry_id: int,
    request: DiaryEntryUpdateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> DiaryEntryDetail:
    return diary_service.update_entry(user_id=current_user.id, entry_id=entry_id, request=request)


@router.delete("/entries/{entry_id}", response_model=DeleteResponse)
def delete_entry(
    entry_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> DeleteResponse:
    return DeleteResponse(
        status="ok",
        deleted=diary_service.delete_entry(user_id=current_user.id, entry_id=entry_id),
    )


@router.post("/entries/{entry_id}/images", response_model=DiaryImageUploadResponse)
async def upload_entry_image(
    entry_id: int,
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
) -> DiaryImageUploadResponse:
    attachment = await diary_service.save_image(
        user_id=current_user.id,
        entry_id=entry_id,
        file=file,
    )
    return DiaryImageUploadResponse(attachment=attachment)


@router.delete("/images/{image_id}", response_model=DeleteResponse)
def delete_entry_image(
    image_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> DeleteResponse:
    return DeleteResponse(
        status="ok",
        deleted=diary_service.delete_image(user_id=current_user.id, image_id=image_id),
    )


__all__ = ["router"]
