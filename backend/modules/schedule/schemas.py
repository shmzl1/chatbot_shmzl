"""Schemas for the local schedule MVP."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


ScheduleItemType = Literal["task", "study_point", "review_point", "habit"]
ScheduleOccurrenceStatus = Literal["pending", "done", "skipped", "postponed", "overdue"]
ScheduleActionResult = Literal["done", "skipped", "postponed"]


def clean_tags(tags: list[str]) -> list[str]:
    result: list[str] = []
    for tag in tags:
        value = str(tag or "").strip()
        if not value:
            continue
        if len(value) > 30:
            raise ValueError("单个标签长度不能超过 30")
        if value not in result:
            result.append(value)
        if len(result) > 20:
            raise ValueError("标签最多 20 个")
    return result


class ScheduleItemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    note: str = Field(default="", max_length=10000)
    item_type: ScheduleItemType = "task"
    priority: int = Field(default=3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    estimated_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    scheduled_date: date
    scheduled_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")

    class Config:
        extra = "forbid"

    @validator("title")
    def clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("标题不能为空")
        return cleaned

    @validator("note")
    def clean_note(cls, value: str) -> str:
        return str(value or "").strip()

    @validator("tags")
    def validate_tags(cls, value: list[str]) -> list[str]:
        return clean_tags(value)

    @validator("scheduled_time")
    def validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        parts = value.split(":")
        if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("时间必须是 HH:MM")
        hour, minute = parts
        if int(hour) > 23 or int(minute) > 59:
            raise ValueError("时间必须是 HH:MM")
        return value


class ScheduleItemUpdateRequest(ScheduleItemCreateRequest):
    pass


class SchedulePostponeRequest(BaseModel):
    scheduled_date: date
    scheduled_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")

    class Config:
        extra = "forbid"

    @validator("scheduled_time")
    def validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        parts = value.split(":")
        if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("时间必须是 HH:MM")
        hour, minute = parts
        if int(hour) > 23 or int(minute) > 59:
            raise ValueError("时间必须是 HH:MM")
        return value


class ScheduleOccurrence(BaseModel):
    id: int
    item_id: int
    scheduled_date: str
    scheduled_time: Optional[str] = None
    status: ScheduleOccurrenceStatus
    completed_at: Optional[str] = None
    source_occurrence_id: Optional[int] = None
    created_at: str
    updated_at: str


class ScheduleItemSummary(BaseModel):
    id: int
    title: str
    note: str = ""
    item_type: ScheduleItemType
    priority: int
    tags: list[str] = Field(default_factory=list)
    estimated_minutes: Optional[int] = None
    current_occurrence: ScheduleOccurrence
    created_at: str
    updated_at: str


class ScheduleItemDetail(ScheduleItemSummary):
    occurrences: list[ScheduleOccurrence] = Field(default_factory=list)


class ScheduleItemListResponse(BaseModel):
    items: list[ScheduleItemSummary] = Field(default_factory=list)
    total: int = 0


class ScheduleStatusCounts(BaseModel):
    pending: int = 0
    done: int = 0
    skipped: int = 0
    postponed: int = 0
    overdue: int = 0


class ScheduleTypeCounts(BaseModel):
    task: int = 0
    study_point: int = 0
    review_point: int = 0
    habit: int = 0


class ScheduleDayResponse(BaseModel):
    date: str
    occurrences: list[ScheduleItemSummary] = Field(default_factory=list)
    status_counts: ScheduleStatusCounts = Field(default_factory=ScheduleStatusCounts)
    type_counts: ScheduleTypeCounts = Field(default_factory=ScheduleTypeCounts)
    total: int = 0
    completion_rate: float = 0


class ScheduleCalendarDay(BaseModel):
    date: str
    total: int = 0
    pending: int = 0
    done: int = 0
    skipped: int = 0
    postponed: int = 0
    overdue: int = 0


class ScheduleCalendarResponse(BaseModel):
    month: str
    days: list[ScheduleCalendarDay] = Field(default_factory=list)


class SchedulePostponeResponse(BaseModel):
    old_occurrence: ScheduleOccurrence
    new_occurrence: ScheduleOccurrence
    item: ScheduleItemDetail
