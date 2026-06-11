"""Repository for diary entries and image metadata."""

import json
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from psycopg.types.json import Json

from modules.diary.schemas import DiaryAttachment, DiaryEntryDetail, DiaryEntryListItem
from services.database_service import database_service


def _as_text(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class DiaryRepository:
    def list_entries(
        self,
        *,
        user_id: int,
        keyword: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        mood: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DiaryEntryListItem]:
        database_service.ensure_ready()
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)
        clauses = ["e.user_id = %s", "e.is_deleted = FALSE"]
        params: List[Any] = [user_id]

        if keyword:
            value = f"%{keyword.strip()}%"
            clauses.append("(e.title ILIKE %s OR e.content_markdown ILIKE %s)")
            params.extend([value, value])
        if date_from:
            clauses.append("e.entry_date >= %s")
            params.append(date_from)
        if date_to:
            clauses.append("e.entry_date <= %s")
            params.append(date_to)
        if mood:
            clauses.append("e.mood = %s")
            params.append(mood.strip())
        if tag:
            clauses.append("e.tags_json ? %s")
            params.append(tag.strip())

        params.extend([safe_limit, safe_offset])
        where = " AND ".join(clauses)
        with database_service._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    e.*,
                    (
                        SELECT COUNT(*)
                        FROM diary_attachments a
                        WHERE a.entry_id = e.id
                          AND a.is_deleted = FALSE
                    ) AS image_count
                FROM diary_entries e
                WHERE {where}
                ORDER BY e.entry_date DESC, e.updated_at DESC, e.id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_list_item(row) for row in rows]

    def create_entry(
        self,
        *,
        user_id: int,
        title: str,
        content_markdown: str,
        entry_date: date,
        mood: str,
        tags: List[str],
    ) -> DiaryEntryDetail:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO diary_entries (
                    user_id,
                    title,
                    content_markdown,
                    entry_date,
                    mood,
                    tags_json
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (user_id, title, content_markdown, entry_date, mood, Json(tags)),
            ).fetchone()
        return self.get_entry(user_id=user_id, entry_id=int(row["id"]))

    def get_entry(self, *, user_id: int, entry_id: int) -> DiaryEntryDetail:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM diary_entries
                WHERE id = %s
                  AND user_id = %s
                  AND is_deleted = FALSE
                LIMIT 1
                """,
                (entry_id, user_id),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Diary entry not found")
            attachments = connection.execute(
                """
                SELECT *
                FROM diary_attachments
                WHERE entry_id = %s
                  AND user_id = %s
                  AND is_deleted = FALSE
                ORDER BY created_at ASC, id ASC
                """,
                (entry_id, user_id),
            ).fetchall()
        return self._row_to_detail(row, attachments)

    def update_entry(
        self,
        *,
        user_id: int,
        entry_id: int,
        title: str,
        content_markdown: str,
        entry_date: date,
        mood: str,
        tags: List[str],
    ) -> DiaryEntryDetail:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            row = connection.execute(
                """
                UPDATE diary_entries
                SET title = %s,
                    content_markdown = %s,
                    entry_date = %s,
                    mood = %s,
                    tags_json = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND user_id = %s
                  AND is_deleted = FALSE
                RETURNING id
                """,
                (title, content_markdown, entry_date, mood, Json(tags), entry_id, user_id),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Diary entry not found")
        return self.get_entry(user_id=user_id, entry_id=entry_id)

    def soft_delete_entry(self, *, user_id: int, entry_id: int) -> int:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            row = connection.execute(
                """
                UPDATE diary_entries
                SET is_deleted = TRUE,
                    deleted_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND user_id = %s
                  AND is_deleted = FALSE
                RETURNING id
                """,
                (entry_id, user_id),
            ).fetchone()
            if row:
                connection.execute(
                    """
                    UPDATE diary_attachments
                    SET is_deleted = TRUE,
                        deleted_at = NOW()
                    WHERE entry_id = %s
                      AND user_id = %s
                      AND is_deleted = FALSE
                    """,
                    (entry_id, user_id),
                )
        return 1 if row else 0

    def create_attachment(
        self,
        *,
        user_id: int,
        entry_id: int,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        storage_path: str,
        public_url: str,
    ) -> DiaryAttachment:
        self.get_entry(user_id=user_id, entry_id=entry_id)
        with database_service._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO diary_attachments (
                    entry_id,
                    user_id,
                    filename,
                    original_filename,
                    content_type,
                    file_size,
                    storage_path,
                    public_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    entry_id,
                    user_id,
                    filename,
                    original_filename,
                    content_type,
                    file_size,
                    storage_path,
                    public_url,
                ),
            ).fetchone()
        return self._row_to_attachment(row)

    def soft_delete_attachment(self, *, user_id: int, image_id: int) -> int:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            row = connection.execute(
                """
                UPDATE diary_attachments
                SET is_deleted = TRUE,
                    deleted_at = NOW()
                WHERE id = %s
                  AND user_id = %s
                  AND is_deleted = FALSE
                RETURNING id
                """,
                (image_id, user_id),
            ).fetchone()
        return 1 if row else 0

    def _row_to_list_item(self, row: Dict[str, Any]) -> DiaryEntryListItem:
        content = str(row["content_markdown"] or "")
        return DiaryEntryListItem(
            id=int(row["id"]),
            title=str(row["title"] or ""),
            content_excerpt=content[:180],
            entry_date=_as_text(row["entry_date"]),
            mood=str(row["mood"] or ""),
            tags=self._tags(row["tags_json"], row["id"]),
            image_count=int(row.get("image_count") or 0),
            created_at=_as_text(row["created_at"]),
            updated_at=_as_text(row["updated_at"]),
        )

    def _row_to_detail(
        self,
        row: Dict[str, Any],
        attachments: List[Dict[str, Any]],
    ) -> DiaryEntryDetail:
        return DiaryEntryDetail(
            id=int(row["id"]),
            title=str(row["title"] or ""),
            content_markdown=str(row["content_markdown"] or ""),
            entry_date=_as_text(row["entry_date"]),
            mood=str(row["mood"] or ""),
            tags=self._tags(row["tags_json"], row["id"]),
            attachments=[self._row_to_attachment(item) for item in attachments],
            created_at=_as_text(row["created_at"]),
            updated_at=_as_text(row["updated_at"]),
        )

    def _row_to_attachment(self, row: Dict[str, Any]) -> DiaryAttachment:
        return DiaryAttachment(
            id=int(row["id"]),
            entry_id=int(row["entry_id"]),
            filename=str(row["filename"]),
            original_filename=str(row["original_filename"] or ""),
            content_type=str(row["content_type"]),
            file_size=int(row["file_size"]),
            public_url=str(row["public_url"]),
            created_at=_as_text(row["created_at"]),
        )

    def _tags(self, value: Any, entry_id: int) -> List[str]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"diary_entries.tags_json for entry {entry_id} is invalid JSON.",
                ) from exc
        if not isinstance(value, list):
            raise HTTPException(
                status_code=500,
                detail=f"diary_entries.tags_json for entry {entry_id} must be a list.",
            )
        return [str(item) for item in value]


diary_repository = DiaryRepository()
