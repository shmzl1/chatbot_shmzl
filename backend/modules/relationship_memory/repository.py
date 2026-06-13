"""Repository for persisted relationship memory events."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from modules.relationship_memory.schemas import (
    RelationshipMemoryCreateRequest,
    RelationshipMemoryEvent,
)
from services.database_service import database_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _row(row: Any) -> Dict[str, Any]:
    return dict(row)


class RelationshipMemoryRepository:
    def create(self, request: RelationshipMemoryCreateRequest) -> RelationshipMemoryEvent:
        database_service.ensure_ready()
        now = _now()
        with database_service._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO relationship_memory_events (
                    character_id,
                    source_type,
                    source_id,
                    source_turn_id,
                    memory_type,
                    content,
                    evidence,
                    importance,
                    is_pinned,
                    is_editable,
                    read_policy,
                    status,
                    expires_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.character_id,
                    request.source_type,
                    request.source_id,
                    request.source_turn_id,
                    request.memory_type,
                    request.content,
                    _json(request.evidence),
                    request.importance,
                    int(request.is_pinned),
                    int(request.is_editable),
                    request.read_policy,
                    request.status,
                    request.expires_at,
                    now,
                    now,
                ),
            )
            event_id = int(cursor.lastrowid)
            row = connection.execute(
                "SELECT * FROM relationship_memory_events WHERE id = ?",
                (event_id,),
            ).fetchone()
        return self._row_to_event(row)

    def list_active(self, *, character_id: str, limit: int = 100) -> List[RelationshipMemoryEvent]:
        database_service.ensure_ready()
        safe_limit = max(1, min(limit, 500))
        now = _now()
        with database_service._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM relationship_memory_events
                WHERE character_id = ?
                  AND is_active = 1
                  AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY importance DESC, updated_at DESC, id DESC
                LIMIT ?
                """,
                (character_id, now, safe_limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def list_prompt_events(self, *, character_id: str, limit: int = 5) -> List[RelationshipMemoryEvent]:
        database_service.ensure_ready()
        safe_limit = max(0, min(limit, 100))
        now = _now()
        with database_service._connect() as connection:
            pinned_rows = connection.execute(
                """
                SELECT *
                FROM relationship_memory_events
                WHERE character_id = ?
                  AND is_active = 1
                  AND status = 'active'
                  AND (is_pinned = 1 OR read_policy = 'always')
                  AND read_policy <> 'never'
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY importance DESC, updated_at DESC, id DESC
                """,
                (character_id, now),
            ).fetchall()
            normal_rows = connection.execute(
                """
                SELECT *
                FROM relationship_memory_events
                WHERE character_id = ?
                  AND is_active = 1
                  AND status = 'active'
                  AND is_pinned = 0
                  AND read_policy = 'relevant'
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY importance DESC, updated_at DESC, id DESC
                LIMIT ?
                """,
                (character_id, now, safe_limit),
            ).fetchall()
        return [self._row_to_event(row) for row in [*pinned_rows, *normal_rows]]

    def deactivate(self, event_id: int) -> Optional[RelationshipMemoryEvent]:
        database_service.ensure_ready()
        with database_service._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE relationship_memory_events
                SET is_active = 0,
                    status = 'archived',
                    updated_at = ?
                WHERE id = ?
                """,
                (_now(), event_id),
            )
            if cursor.rowcount <= 0:
                return None
            row = connection.execute(
                "SELECT * FROM relationship_memory_events WHERE id = ?",
                (event_id,),
            ).fetchone()
        return self._row_to_event(row) if row else None

    def mark_used(self, event_ids: List[int]) -> None:
        if not event_ids:
            return
        database_service.ensure_ready()
        placeholders = ",".join("?" for _ in event_ids)
        with database_service._connect() as connection:
            connection.execute(
                f"""
                UPDATE relationship_memory_events
                SET last_used_at = ?,
                    use_count = use_count + 1
                WHERE id IN ({placeholders})
                """,
                tuple([_now(), *event_ids]),
            )

    def debug(
        self,
        *,
        character_id: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        database_service.ensure_ready()
        safe_limit = max(1, min(limit, 500))
        clauses = []
        params: List[Any] = []
        if character_id:
            clauses.append("character_id = ?")
            params.append(character_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with database_service._connect() as connection:
            total_row = connection.execute(
                f"SELECT COUNT(*) AS count FROM relationship_memory_events {where}",
                tuple(params),
            ).fetchone()
            active_where = f"{where} AND is_active = 1" if where else "WHERE is_active = 1"
            active_row = connection.execute(
                f"SELECT COUNT(*) AS count FROM relationship_memory_events {active_where}",
                tuple(params),
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT *
                FROM relationship_memory_events
                {where}
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                tuple([*params, safe_limit]),
            ).fetchall()

        return {
            "character_id": character_id,
            "total_count": int(total_row["count"]) if total_row else 0,
            "active_count": int(active_row["count"]) if active_row else 0,
            "events": [self._row_to_event(row) for row in rows],
        }

    def _row_to_event(self, raw_row: Any) -> RelationshipMemoryEvent:
        row = _row(raw_row)
        evidence = row["evidence"]
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"relationship_memory_events.evidence for event {row['id']} is invalid JSON.",
                ) from exc
        if evidence is None:
            evidence = {}
        if not isinstance(evidence, dict):
            raise HTTPException(
                status_code=500,
                detail=f"relationship_memory_events.evidence for event {row['id']} must be an object.",
            )
        return RelationshipMemoryEvent(
            id=row["id"],
            character_id=row["character_id"],
            source_type=row["source_type"],
            source_id=row["source_id"],
            source_turn_id=row["source_turn_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            evidence=evidence,
            importance=row["importance"],
            is_active=bool(row["is_active"]),
            is_pinned=bool(row.get("is_pinned", False)),
            is_editable=bool(row.get("is_editable", True)),
            read_policy=str(row.get("read_policy") or "relevant"),
            status=str(row.get("status") or "active"),
            expires_at=self._as_text(row["expires_at"]) if row.get("expires_at") else None,
            last_used_at=self._as_text(row["last_used_at"]) if row.get("last_used_at") else None,
            use_count=int(row.get("use_count") or 0),
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
        )

    def _as_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


relationship_memory_repository = RelationshipMemoryRepository()
