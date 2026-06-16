"""API routes for the local schedule MVP."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from core.schemas import DeleteResponse, UserRecord
from modules.schedule.schemas import (
    ScheduleCalendarResponse,
    ScheduleDayResponse,
    ScheduleItemCreateRequest,
    ScheduleItemDetail,
    ScheduleItemListResponse,
    ScheduleItemType,
    ScheduleItemUpdateRequest,
    ScheduleOccurrenceStatus,
    SchedulePostponeRequest,
    SchedulePostponeResponse,
)
from modules.schedule.service import schedule_service
from services.auth_service import get_current_user


router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/items", response_model=ScheduleItemListResponse)
def list_items(
    keyword: Optional[str] = None,
    item_type: Optional[ScheduleItemType] = None,
    status: Optional[ScheduleOccurrenceStatus] = None,
    tag: Optional[str] = None,
    priority: Optional[int] = Query(default=None, ge=1, le=5),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemListResponse:
    return schedule_service.list_items(
        user_id=current_user.id,
        keyword=keyword,
        item_type=item_type,
        status=status,
        tag=tag,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.post("/items", response_model=ScheduleItemDetail)
def create_item(
    request: ScheduleItemCreateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemDetail:
    return schedule_service.create_item(user_id=current_user.id, request=request)


@router.get("/items/{item_id}", response_model=ScheduleItemDetail)
def get_item(
    item_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemDetail:
    return schedule_service.get_item(user_id=current_user.id, item_id=item_id)


@router.put("/items/{item_id}", response_model=ScheduleItemDetail)
def update_item(
    item_id: int,
    request: ScheduleItemUpdateRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemDetail:
    return schedule_service.update_item(user_id=current_user.id, item_id=item_id, request=request)


@router.delete("/items/{item_id}", response_model=DeleteResponse)
def delete_item(
    item_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> DeleteResponse:
    return DeleteResponse(
        status="ok",
        deleted=schedule_service.delete_item(user_id=current_user.id, item_id=item_id),
    )


@router.get("/today", response_model=ScheduleDayResponse)
def get_day(
    date_value: Optional[date] = Query(default=None, alias="date"),
    item_type: Optional[ScheduleItemType] = None,
    status: Optional[ScheduleOccurrenceStatus] = None,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleDayResponse:
    return schedule_service.get_day(
        user_id=current_user.id,
        selected_date=date_value,
        item_type=item_type,
        status=status,
    )


@router.get("/calendar", response_model=ScheduleCalendarResponse)
def get_calendar(
    month: str,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleCalendarResponse:
    return schedule_service.get_calendar(user_id=current_user.id, month=month)


@router.post("/occurrences/{occurrence_id}/complete", response_model=ScheduleItemDetail)
def complete_occurrence(
    occurrence_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemDetail:
    return schedule_service.complete_occurrence(user_id=current_user.id, occurrence_id=occurrence_id)


@router.post("/occurrences/{occurrence_id}/skip", response_model=ScheduleItemDetail)
def skip_occurrence(
    occurrence_id: int,
    current_user: UserRecord = Depends(get_current_user),
) -> ScheduleItemDetail:
    return schedule_service.skip_occurrence(user_id=current_user.id, occurrence_id=occurrence_id)


@router.post("/occurrences/{occurrence_id}/postpone", response_model=SchedulePostponeResponse)
def postpone_occurrence(
    occurrence_id: int,
    request: SchedulePostponeRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> SchedulePostponeResponse:
    return schedule_service.postpone_occurrence(
        user_id=current_user.id,
        occurrence_id=occurrence_id,
        request=request,
    )


__all__ = ["router"]
