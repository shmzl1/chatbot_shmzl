"""Service layer for the local schedule MVP."""

from calendar import monthrange
from datetime import date
from typing import Optional

from fastapi import HTTPException

from modules.schedule.repository import schedule_repository
from modules.schedule.schemas import (
    ScheduleCalendarDay,
    ScheduleCalendarResponse,
    ScheduleDayResponse,
    ScheduleItemCreateRequest,
    ScheduleItemDetail,
    ScheduleItemListResponse,
    ScheduleItemSummary,
    ScheduleItemUpdateRequest,
    SchedulePostponeRequest,
    SchedulePostponeResponse,
    ScheduleStatusCounts,
    ScheduleTypeCounts,
)


class ScheduleService:
    def create_item(self, *, user_id: int, request: ScheduleItemCreateRequest) -> ScheduleItemDetail:
        return schedule_repository.create_item(
            user_id=user_id,
            title=request.title,
            note=request.note,
            item_type=request.item_type,
            priority=request.priority,
            tags=request.tags,
            estimated_minutes=request.estimated_minutes,
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
            today=date.today(),
        )

    def get_item(self, *, user_id: int, item_id: int) -> ScheduleItemDetail:
        self.mark_overdue(user_id=user_id)
        return schedule_repository.get_item(user_id=user_id, item_id=item_id)

    def list_items(
        self,
        *,
        user_id: int,
        keyword: Optional[str] = None,
        item_type: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        priority: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ScheduleItemListResponse:
        self.mark_overdue(user_id=user_id)
        items, total = schedule_repository.list_items(
            user_id=user_id,
            keyword=self._clean_optional(keyword),
            item_type=self._clean_optional(item_type),
            status=self._clean_optional(status),
            tag=self._clean_optional(tag),
            priority=priority,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        return ScheduleItemListResponse(items=items, total=total)

    def update_item(
        self,
        *,
        user_id: int,
        item_id: int,
        request: ScheduleItemUpdateRequest,
    ) -> ScheduleItemDetail:
        return schedule_repository.update_item(
            user_id=user_id,
            item_id=item_id,
            title=request.title,
            note=request.note,
            item_type=request.item_type,
            priority=request.priority,
            tags=request.tags,
            estimated_minutes=request.estimated_minutes,
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
            today=date.today(),
        )

    def delete_item(self, *, user_id: int, item_id: int) -> int:
        deleted = schedule_repository.soft_delete_item(user_id=user_id, item_id=item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="任务不存在")
        return deleted

    def get_day(
        self,
        *,
        user_id: int,
        selected_date: Optional[date] = None,
        item_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ScheduleDayResponse:
        self.mark_overdue(user_id=user_id)
        resolved_date = selected_date or date.today()
        occurrences = schedule_repository.list_day_occurrences(
            user_id=user_id,
            scheduled_date=resolved_date,
            item_type=self._clean_optional(item_type),
            status=self._clean_optional(status),
        )
        return self._day_response(resolved_date, occurrences)

    def get_calendar(self, *, user_id: int, month: str) -> ScheduleCalendarResponse:
        self.mark_overdue(user_id=user_id)
        year, month_number = self._parse_month(month)
        last_day = monthrange(year, month_number)[1]
        first = date(year, month_number, 1)
        last = date(year, month_number, last_day)
        rows = schedule_repository.get_calendar_summary(
            user_id=user_id,
            date_from=first,
            date_to=last,
        )
        by_date = {
            date(year, month_number, day).isoformat(): {
                "date": date(year, month_number, day).isoformat(),
                "total": 0,
                "pending": 0,
                "done": 0,
                "skipped": 0,
                "postponed": 0,
                "overdue": 0,
            }
            for day in range(1, last_day + 1)
        }
        for row in rows:
            target = by_date.get(str(row["scheduled_date"]))
            if not target:
                continue
            status = str(row["status"])
            count = int(row["count"])
            target["total"] += count
            if status in ("pending", "done", "skipped", "postponed", "overdue"):
                target[status] += count
        return ScheduleCalendarResponse(
            month=f"{year:04d}-{month_number:02d}",
            days=[ScheduleCalendarDay(**by_date[key]) for key in sorted(by_date)],
        )

    def complete_occurrence(self, *, user_id: int, occurrence_id: int) -> ScheduleItemDetail:
        return schedule_repository.complete_occurrence(user_id=user_id, occurrence_id=occurrence_id)

    def skip_occurrence(self, *, user_id: int, occurrence_id: int) -> ScheduleItemDetail:
        return schedule_repository.skip_occurrence(user_id=user_id, occurrence_id=occurrence_id)

    def postpone_occurrence(
        self,
        *,
        user_id: int,
        occurrence_id: int,
        request: SchedulePostponeRequest,
    ) -> SchedulePostponeResponse:
        old_occurrence, new_occurrence, item = schedule_repository.postpone_occurrence(
            user_id=user_id,
            occurrence_id=occurrence_id,
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
        )
        return SchedulePostponeResponse(
            old_occurrence=old_occurrence,
            new_occurrence=new_occurrence,
            item=item,
        )

    def mark_overdue(self, *, user_id: int) -> int:
        return schedule_repository.mark_overdue(user_id=user_id, today=date.today())

    def _day_response(self, selected_date: date, occurrences: list[ScheduleItemSummary]) -> ScheduleDayResponse:
        status_counts = ScheduleStatusCounts()
        type_counts = ScheduleTypeCounts()
        for item in occurrences:
            status = item.current_occurrence.status
            setattr(status_counts, status, getattr(status_counts, status) + 1)
            setattr(type_counts, item.item_type, getattr(type_counts, item.item_type) + 1)
        total = len(occurrences)
        completion_rate = (status_counts.done / total) if total else 0
        return ScheduleDayResponse(
            date=selected_date.isoformat(),
            occurrences=occurrences,
            status_counts=status_counts,
            type_counts=type_counts,
            total=total,
            completion_rate=completion_rate,
        )

    def _parse_month(self, value: str) -> tuple[int, int]:
        if not value or len(value) != 7 or value[4] != "-":
            raise HTTPException(status_code=422, detail="month 必须是 YYYY-MM")
        try:
            year = int(value[:4])
            month_number = int(value[5:7])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="month 必须是 YYYY-MM") from exc
        if month_number < 1 or month_number > 12:
            raise HTTPException(status_code=422, detail="month 必须是 YYYY-MM")
        return year, month_number

    def _clean_optional(self, value: Optional[str]) -> Optional[str]:
        cleaned = str(value or "").strip()
        return cleaned or None


schedule_service = ScheduleService()
