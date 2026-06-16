"""Repository for local schedule items and occurrences."""

import json
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException

from modules.schedule.schemas import ScheduleItemDetail, ScheduleItemSummary, ScheduleOccurrence
from services.database_service import database_service


ACTIVE_STATUSES = ("pending", "overdue")
TERMINAL_STATUSES = ("done", "skipped", "postponed")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_text(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _row(row: Any) -> dict[str, Any]:
    return dict(row)


class ScheduleRepository:
    def create_item(
        self,
        *,
        user_id: int,
        title: str,
        note: str,
        item_type: str,
        priority: int,
        tags: list[str],
        estimated_minutes: Optional[int],
        scheduled_date: date,
        scheduled_time: Optional[str],
        today: date,
    ) -> ScheduleItemDetail:
        database_service.ensure_ready()
        now = _now()
        status = self._status_for_date(scheduled_date, today)
        with database_service._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO schedule_items (
                        user_id,
                        title,
                        note,
                        item_type,
                        priority,
                        tags_json,
                        estimated_minutes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, title, note, item_type, priority, _json(tags), estimated_minutes, now, now),
                )
                item_id = int(cursor.lastrowid)
                connection.execute(
                    """
                    INSERT INTO schedule_occurrences (
                        item_id,
                        user_id,
                        scheduled_date,
                        scheduled_time,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item_id, user_id, _as_text(scheduled_date), scheduled_time, status, now, now),
                )
            except Exception:
                connection.rollback()
                raise
        return self.get_item(user_id=user_id, item_id=item_id)

    def get_item(self, *, user_id: int, item_id: int) -> ScheduleItemDetail:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            item_row = connection.execute(
                """
                SELECT *
                FROM schedule_items
                WHERE id = ?
                  AND user_id = ?
                  AND is_deleted = 0
                LIMIT 1
                """,
                (item_id, user_id),
            ).fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="任务不存在")
            occurrence_rows = connection.execute(
                """
                SELECT *
                FROM schedule_occurrences
                WHERE item_id = ?
                  AND user_id = ?
                ORDER BY
                    CASE status
                        WHEN 'pending' THEN 0
                        WHEN 'overdue' THEN 1
                        ELSE 2
                    END,
                    scheduled_date DESC,
                    COALESCE(scheduled_time, '') DESC,
                    id DESC
                """,
                (item_id, user_id),
            ).fetchall()
        return self._row_to_detail(item_row, occurrence_rows)

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
    ) -> tuple[list[ScheduleItemSummary], int]:
        database_service.ensure_ready()
        clauses = ["i.user_id = ?", "i.is_deleted = 0"]
        params: list[Any] = [user_id]
        if keyword:
            value = f"%{keyword.strip()}%"
            clauses.append("(LOWER(i.title) LIKE LOWER(?) OR LOWER(i.note) LIKE LOWER(?))")
            params.extend([value, value])
        if item_type:
            clauses.append("i.item_type = ?")
            params.append(item_type)
        if status:
            clauses.append("o.status = ?")
            params.append(status)
        if tag:
            clauses.append("i.tags_json LIKE ?")
            params.append(f'%"{tag.strip()}"%')
        if priority:
            clauses.append("i.priority = ?")
            params.append(priority)
        if date_from:
            clauses.append("o.scheduled_date >= ?")
            params.append(_as_text(date_from))
        if date_to:
            clauses.append("o.scheduled_date <= ?")
            params.append(_as_text(date_to))
        where = " AND ".join(clauses)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)
        with database_service._connect() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(DISTINCT i.id) AS count
                FROM schedule_items i
                JOIN schedule_occurrences o ON o.item_id = i.id AND o.user_id = i.user_id
                WHERE {where}
                """,
                tuple(params),
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT i.*, o.id AS occurrence_id
                FROM schedule_items i
                JOIN schedule_occurrences o ON o.item_id = i.id AND o.user_id = i.user_id
                WHERE {where}
                GROUP BY i.id
                ORDER BY i.updated_at DESC, i.id DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [safe_limit, safe_offset]),
            ).fetchall()
        items = [self.get_item(user_id=user_id, item_id=int(row["id"])) for row in rows]
        return [self._detail_to_summary(item) for item in items], int(count_row["count"]) if count_row else 0

    def update_item(
        self,
        *,
        user_id: int,
        item_id: int,
        title: str,
        note: str,
        item_type: str,
        priority: int,
        tags: list[str],
        estimated_minutes: Optional[int],
        scheduled_date: date,
        scheduled_time: Optional[str],
        today: date,
    ) -> ScheduleItemDetail:
        database_service.ensure_ready()
        now = _now()
        with database_service._connect() as connection:
            item = self._get_item_row(connection, user_id=user_id, item_id=item_id)
            occurrence = self._get_current_mutable_occurrence(connection, user_id=user_id, item_id=int(item["id"]))
            if not occurrence:
                raise HTTPException(status_code=409, detail="终态任务不能直接改期，请新建任务。")
            new_status = self._status_for_date(scheduled_date, today)
            connection.execute(
                """
                UPDATE schedule_items
                SET title = ?,
                    note = ?,
                    item_type = ?,
                    priority = ?,
                    tags_json = ?,
                    estimated_minutes = ?,
                    updated_at = ?
                WHERE id = ?
                  AND user_id = ?
                  AND is_deleted = 0
                """,
                (title, note, item_type, priority, _json(tags), estimated_minutes, now, item_id, user_id),
            )
            connection.execute(
                """
                UPDATE schedule_occurrences
                SET scheduled_date = ?,
                    scheduled_time = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (_as_text(scheduled_date), scheduled_time, new_status, now, int(occurrence["id"]), user_id),
            )
        return self.get_item(user_id=user_id, item_id=item_id)

    def soft_delete_item(self, *, user_id: int, item_id: int) -> int:
        database_service.ensure_ready()
        now = _now()
        with database_service._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE schedule_items
                SET is_deleted = 1,
                    deleted_at = ?,
                    updated_at = ?
                WHERE id = ?
                  AND user_id = ?
                  AND is_deleted = 0
                """,
                (now, now, item_id, user_id),
            )
        return 1 if cursor.rowcount else 0

    def list_day_occurrences(
        self,
        *,
        user_id: int,
        scheduled_date: date,
        item_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[ScheduleItemSummary]:
        database_service.ensure_ready()
        clauses = ["i.user_id = ?", "i.is_deleted = 0", "o.scheduled_date = ?"]
        params: list[Any] = [user_id, _as_text(scheduled_date)]
        if item_type:
            clauses.append("i.item_type = ?")
            params.append(item_type)
        if status:
            clauses.append("o.status = ?")
            params.append(status)
        where = " AND ".join(clauses)
        with database_service._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    i.id AS item_id,
                    i.title,
                    i.note,
                    i.item_type,
                    i.priority,
                    i.tags_json,
                    i.estimated_minutes,
                    i.created_at AS item_created_at,
                    i.updated_at AS item_updated_at,
                    o.id AS occurrence_id,
                    o.scheduled_date,
                    o.scheduled_time,
                    o.status,
                    o.completed_at,
                    o.source_occurrence_id,
                    o.created_at AS occurrence_created_at,
                    o.updated_at AS occurrence_updated_at
                FROM schedule_occurrences o
                JOIN schedule_items i ON i.id = o.item_id AND i.user_id = o.user_id
                WHERE {where}
                ORDER BY
                    COALESCE(o.scheduled_time, '99:99') ASC,
                    CASE o.status
                        WHEN 'pending' THEN 0
                        WHEN 'overdue' THEN 1
                        WHEN 'done' THEN 2
                        WHEN 'postponed' THEN 3
                        ELSE 4
                    END,
                    i.priority ASC,
                    o.id ASC
                """,
                tuple(params),
            ).fetchall()
        return [self._joined_row_to_summary(row) for row in rows]

    def get_calendar_summary(
        self,
        *,
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    o.scheduled_date,
                    o.status,
                    COUNT(*) AS count
                FROM schedule_occurrences o
                JOIN schedule_items i ON i.id = o.item_id AND i.user_id = o.user_id
                WHERE o.user_id = ?
                  AND i.is_deleted = 0
                  AND o.scheduled_date >= ?
                  AND o.scheduled_date <= ?
                GROUP BY o.scheduled_date, o.status
                """,
                (user_id, _as_text(date_from), _as_text(date_to)),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_overdue(self, *, user_id: int, today: date) -> int:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE schedule_occurrences
                SET status = 'overdue',
                    updated_at = ?
                WHERE user_id = ?
                  AND status = 'pending'
                  AND scheduled_date < ?
                  AND item_id IN (
                    SELECT id
                    FROM schedule_items
                    WHERE user_id = ?
                      AND is_deleted = 0
                  )
                """,
                (_now(), user_id, _as_text(today), user_id),
            )
        return cursor.rowcount

    def complete_occurrence(self, *, user_id: int, occurrence_id: int) -> ScheduleItemDetail:
        return self._finish_occurrence(user_id=user_id, occurrence_id=occurrence_id, status="done", result="done")

    def skip_occurrence(self, *, user_id: int, occurrence_id: int) -> ScheduleItemDetail:
        return self._finish_occurrence(user_id=user_id, occurrence_id=occurrence_id, status="skipped", result="skipped")

    def postpone_occurrence(
        self,
        *,
        user_id: int,
        occurrence_id: int,
        scheduled_date: date,
        scheduled_time: Optional[str],
    ) -> tuple[ScheduleOccurrence, ScheduleOccurrence, ScheduleItemDetail]:
        database_service.ensure_ready()
        now = _now()
        with database_service._connect() as connection:
            old = self._get_occurrence_row(connection, user_id=user_id, occurrence_id=occurrence_id)
            if old["status"] not in ACTIVE_STATUSES:
                raise HTTPException(status_code=409, detail="该任务状态已结束，不能重复延期。")
            self._validate_postpone_target(old, scheduled_date, scheduled_time)
            connection.execute(
                """
                UPDATE schedule_occurrences
                SET status = 'postponed',
                    updated_at = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (now, occurrence_id, user_id),
            )
            cursor = connection.execute(
                """
                INSERT INTO schedule_occurrences (
                    item_id,
                    user_id,
                    scheduled_date,
                    scheduled_time,
                    status,
                    source_occurrence_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    int(old["item_id"]),
                    user_id,
                    _as_text(scheduled_date),
                    scheduled_time,
                    occurrence_id,
                    now,
                    now,
                ),
            )
            new_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO schedule_completion_logs (occurrence_id, user_id, result, feedback, created_at)
                VALUES (?, ?, 'postponed', '', ?)
                """,
                (occurrence_id, user_id, now),
            )
            old_row = self._get_occurrence_row(connection, user_id=user_id, occurrence_id=occurrence_id)
            new_row = self._get_occurrence_row(connection, user_id=user_id, occurrence_id=new_id)
        item = self.get_item(user_id=user_id, item_id=int(old["item_id"]))
        return self._row_to_occurrence(old_row), self._row_to_occurrence(new_row), item

    def _finish_occurrence(self, *, user_id: int, occurrence_id: int, status: str, result: str) -> ScheduleItemDetail:
        database_service.ensure_ready()
        now = _now()
        with database_service._connect() as connection:
            occurrence = self._get_occurrence_row(connection, user_id=user_id, occurrence_id=occurrence_id)
            if occurrence["status"] not in ACTIVE_STATUSES:
                raise HTTPException(status_code=409, detail="该任务状态已结束，不能重复操作。")
            connection.execute(
                """
                UPDATE schedule_occurrences
                SET status = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (status, now if status == "done" else None, now, occurrence_id, user_id),
            )
            connection.execute(
                """
                INSERT INTO schedule_completion_logs (occurrence_id, user_id, result, feedback, created_at)
                VALUES (?, ?, ?, '', ?)
                """,
                (occurrence_id, user_id, result, now),
            )
        return self.get_item(user_id=user_id, item_id=int(occurrence["item_id"]))

    def _get_item_row(self, connection: Any, *, user_id: int, item_id: int) -> Any:
        row = connection.execute(
            """
            SELECT *
            FROM schedule_items
            WHERE id = ?
              AND user_id = ?
              AND is_deleted = 0
            LIMIT 1
            """,
            (item_id, user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        return row

    def _get_occurrence_row(self, connection: Any, *, user_id: int, occurrence_id: int) -> Any:
        row = connection.execute(
            """
            SELECT o.*
            FROM schedule_occurrences o
            JOIN schedule_items i ON i.id = o.item_id AND i.user_id = o.user_id
            WHERE o.id = ?
              AND o.user_id = ?
              AND i.is_deleted = 0
            LIMIT 1
            """,
            (occurrence_id, user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="任务实例不存在")
        return row

    def _get_current_mutable_occurrence(self, connection: Any, *, user_id: int, item_id: int) -> Any:
        return connection.execute(
            """
            SELECT *
            FROM schedule_occurrences
            WHERE item_id = ?
              AND user_id = ?
              AND status IN ('pending', 'overdue')
            ORDER BY
                CASE status WHEN 'pending' THEN 0 ELSE 1 END,
                scheduled_date DESC,
                COALESCE(scheduled_time, '') DESC,
                id DESC
            LIMIT 1
            """,
            (item_id, user_id),
        ).fetchone()

    def _validate_postpone_target(self, occurrence: Any, scheduled_date: date, scheduled_time: Optional[str]) -> None:
        old_date = str(occurrence["scheduled_date"])
        new_date = _as_text(scheduled_date)
        old_time = occurrence["scheduled_time"]
        if new_date < old_date:
            raise HTTPException(status_code=400, detail="延期日期不能早于原安排。")
        if new_date == old_date:
            if not scheduled_time:
                raise HTTPException(status_code=400, detail="同日延期必须填写更晚的新时间。")
            if old_time and scheduled_time <= old_time:
                raise HTTPException(status_code=400, detail="同日延期的新时间必须晚于原时间。")

    def _status_for_date(self, scheduled_date: date, today: date) -> str:
        return "overdue" if scheduled_date < today else "pending"

    def _row_to_occurrence(self, raw_row: Any) -> ScheduleOccurrence:
        row = _row(raw_row)
        return ScheduleOccurrence(
            id=int(row["id"]),
            item_id=int(row["item_id"]),
            scheduled_date=_as_text(row["scheduled_date"]),
            scheduled_time=row["scheduled_time"],
            status=row["status"],
            completed_at=row["completed_at"],
            source_occurrence_id=row["source_occurrence_id"],
            created_at=_as_text(row["created_at"]),
            updated_at=_as_text(row["updated_at"]),
        )

    def _row_to_detail(self, item_row: Any, occurrence_rows: list[Any]) -> ScheduleItemDetail:
        row = _row(item_row)
        occurrences = [self._row_to_occurrence(item) for item in occurrence_rows]
        if not occurrences:
            raise HTTPException(status_code=500, detail=f"任务 {row['id']} 缺少 occurrence。")
        current_occurrence = occurrences[0]
        return ScheduleItemDetail(
            id=int(row["id"]),
            title=str(row["title"]),
            note=str(row["note"] or ""),
            item_type=row["item_type"],
            priority=int(row["priority"]),
            tags=self._tags(row["tags_json"], int(row["id"])),
            estimated_minutes=row["estimated_minutes"],
            current_occurrence=current_occurrence,
            occurrences=occurrences,
            created_at=_as_text(row["created_at"]),
            updated_at=_as_text(row["updated_at"]),
        )

    def _detail_to_summary(self, detail: ScheduleItemDetail) -> ScheduleItemSummary:
        if hasattr(detail, "model_dump"):
            data = detail.model_dump(exclude={"occurrences"})
        else:
            data = detail.dict(exclude={"occurrences"})
        return ScheduleItemSummary(**data)

    def _joined_row_to_summary(self, raw_row: Any) -> ScheduleItemSummary:
        row = _row(raw_row)
        occurrence = ScheduleOccurrence(
            id=int(row["occurrence_id"]),
            item_id=int(row["item_id"]),
            scheduled_date=_as_text(row["scheduled_date"]),
            scheduled_time=row["scheduled_time"],
            status=row["status"],
            completed_at=row["completed_at"],
            source_occurrence_id=row["source_occurrence_id"],
            created_at=_as_text(row["occurrence_created_at"]),
            updated_at=_as_text(row["occurrence_updated_at"]),
        )
        return ScheduleItemSummary(
            id=int(row["item_id"]),
            title=str(row["title"]),
            note=str(row["note"] or ""),
            item_type=row["item_type"],
            priority=int(row["priority"]),
            tags=self._tags(row["tags_json"], int(row["item_id"])),
            estimated_minutes=row["estimated_minutes"],
            current_occurrence=occurrence,
            created_at=_as_text(row["item_created_at"]),
            updated_at=_as_text(row["item_updated_at"]),
        )

    def _tags(self, value: Any, item_id: int) -> list[str]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"schedule_items.tags_json for item {item_id} is invalid JSON.",
                ) from exc
        if not isinstance(value, list):
            raise HTTPException(
                status_code=500,
                detail=f"schedule_items.tags_json for item {item_id} must be a list.",
            )
        return [str(item) for item in value]


schedule_repository = ScheduleRepository()
