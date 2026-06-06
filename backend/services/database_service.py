import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row
from psycopg.types.json import Json

from core.config import settings
from core.schemas import CandidateReply, ChatSessionSummary, ChatTurnRecord, MemoryRecord
from core.schemas import KnowledgeRecord


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class DatabaseService:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._initialized = False

    def save_chat_turn(
        self,
        *,
        session_id: Optional[str],
        character_id: str,
        user_message: str,
        reply: str,
        emotion: str,
        candidates: List[CandidateReply],
        debug: Dict[str, Any],
    ) -> tuple[str, int]:
        self._ensure_database()
        resolved_session_id = session_id or uuid.uuid4().hex
        now = _now()
        candidates_json = [_model_to_dict(candidate) for candidate in candidates]

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions (id, character_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    character_id = EXCLUDED.character_id,
                    updated_at = EXCLUDED.updated_at
                """,
                (resolved_session_id, character_id, now, now),
            )
            row = connection.execute(
                """
                INSERT INTO chat_turns (
                    session_id,
                    character_id,
                    user_message,
                    reply,
                    emotion,
                    candidates_json,
                    debug_json,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    resolved_session_id,
                    character_id,
                    user_message,
                    reply,
                    emotion,
                    Json(candidates_json),
                    Json(debug),
                    now,
                ),
            ).fetchone()

        return resolved_session_id, int(row["id"])

    def list_sessions(self, limit: int = 50) -> List[ChatSessionSummary]:
        self._ensure_database()
        safe_limit = max(1, min(limit, 200))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.id,
                    s.character_id,
                    s.created_at,
                    s.updated_at,
                    COUNT(t.id) AS turn_count,
                    (
                        SELECT user_message
                        FROM chat_turns
                        WHERE session_id = s.id
                        ORDER BY id DESC
                        LIMIT 1
                    ) AS last_user_message,
                    (
                        SELECT reply
                        FROM chat_turns
                        WHERE session_id = s.id
                        ORDER BY id DESC
                        LIMIT 1
                    ) AS last_reply
                FROM chat_sessions s
                LEFT JOIN chat_turns t ON t.session_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT %s
                """,
                (safe_limit,),
            ).fetchall()

        return [
            ChatSessionSummary(
                id=row["id"],
                character_id=row["character_id"],
                created_at=self._as_text(row["created_at"]),
                updated_at=self._as_text(row["updated_at"]),
                turn_count=row["turn_count"],
                last_user_message=row["last_user_message"],
                last_reply=row["last_reply"],
            )
            for row in rows
        ]

    def list_turns(self, session_id: str) -> List[ChatTurnRecord]:
        self._ensure_database()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    session_id,
                    character_id,
                    user_message,
                    reply,
                    emotion,
                    candidates_json,
                    debug_json,
                    created_at
                FROM chat_turns
                WHERE session_id = %s
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [self._row_to_turn(row) for row in rows]

    def recent_history(self, session_id: Optional[str], limit: int = 10) -> List[Dict[str, str]]:
        if not session_id:
            return []

        self._ensure_database()
        safe_limit = max(1, min(limit, 30))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_message, reply, emotion
                FROM chat_turns
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (session_id, safe_limit),
            ).fetchall()

        history = []
        for row in reversed(rows):
            history.append(
                {
                    "user": row["user_message"],
                    "assistant": row["reply"],
                    "emotion": row["emotion"],
                }
            )
        return history

    def info(self) -> Dict[str, Any]:
        self._ensure_database()
        with self._connect() as connection:
            session_row = connection.execute(
                "SELECT COUNT(*) AS count FROM chat_sessions"
            ).fetchone()
            turn_row = connection.execute("SELECT COUNT(*) AS count FROM chat_turns").fetchone()
            memory_row = connection.execute(
                "SELECT COUNT(*) AS count FROM long_term_memories"
            ).fetchone()
            knowledge_row = connection.execute(
                "SELECT COUNT(*) AS count FROM knowledge_items"
            ).fetchone()
            feedback_row = connection.execute(
                "SELECT COUNT(*) AS count FROM turn_feedback"
            ).fetchone()

        return {
            "database_backend": "postgresql",
            "database_url": self._masked_database_url(),
            "session_count": int(session_row["count"]) if session_row else 0,
            "turn_count": int(turn_row["count"]) if turn_row else 0,
            "memory_count": int(memory_row["count"]) if memory_row else 0,
            "knowledge_count": int(knowledge_row["count"]) if knowledge_row else 0,
            "feedback_count": int(feedback_row["count"]) if feedback_row else 0,
        }

    def is_ready(self) -> bool:
        try:
            self._ensure_database()
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def delete_session(self, session_id: str) -> int:
        self._ensure_database()
        with self._connect() as connection:
            count_row = connection.execute(
                "SELECT COUNT(*) AS count FROM chat_turns WHERE session_id = %s",
                (session_id,),
            ).fetchone()
            deleted = int(count_row["count"]) if count_row else 0
            connection.execute("DELETE FROM chat_turns WHERE session_id = %s", (session_id,))
            connection.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
        return deleted

    def update_turn_debug(self, turn_id: int, debug: Dict[str, Any]) -> None:
        self._ensure_database()
        with self._connect() as connection:
            connection.execute(
                "UPDATE chat_turns SET debug_json = %s WHERE id = %s",
                (Json(debug), turn_id),
            )

    def clear_sessions(self) -> int:
        self._ensure_database()
        with self._connect() as connection:
            count_row = connection.execute("SELECT COUNT(*) AS count FROM chat_turns").fetchone()
            deleted = int(count_row["count"]) if count_row else 0
            connection.execute("DELETE FROM chat_turns")
            connection.execute("DELETE FROM chat_sessions")
        return deleted

    def create_memory(
        self,
        *,
        character_id: str,
        content: str,
        memory_type: str,
        importance: int,
        tags: List[str],
    ) -> MemoryRecord:
        self._ensure_database()
        now = _now()
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO long_term_memories (
                    character_id,
                    memory_type,
                    content,
                    importance,
                    tags_json,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (character_id, memory_type, content, importance, Json(tags), now, now),
            ).fetchone()
        return self._row_to_memory(row)

    def list_memories(
        self,
        *,
        character_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        self._ensure_database()
        safe_limit = max(1, min(limit, 500))
        with self._connect() as connection:
            if character_id:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM long_term_memories
                    WHERE character_id = %s
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT %s
                    """,
                    (character_id, safe_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM long_term_memories
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT %s
                    """,
                    (safe_limit,),
                ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def retrieve_memories(
        self,
        *,
        character_id: str,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []

        memories = self.list_memories(character_id=character_id, limit=300)
        scored = []
        for index, memory in enumerate(memories):
            text = " ".join([memory.content, " ".join(memory.tags), memory.memory_type])
            score = self._score(text, query) + memory.importance
            scored.append((score, index, memory))

        chosen = sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]
        hits: List[Dict[str, Any]] = []
        for score, _, memory in chosen:
            hits.append(
                {
                    "id": f"mem_{memory.id}",
                    "source": "memory",
                    "score": score,
                    "text": memory.content,
                    "payload": {
                        "id": memory.id,
                        "memory_type": memory.memory_type,
                        "content": memory.content,
                        "importance": memory.importance,
                        "tags": memory.tags,
                    },
                }
            )
        return hits

    def mark_memories_used(self, memory_ids: List[int]) -> None:
        if not memory_ids:
            return
        self._ensure_database()
        with self._connect() as connection:
            connection.execute(
                "UPDATE long_term_memories SET last_used_at = %s WHERE id = ANY(%s)",
                (_now(), memory_ids),
            )

    def delete_memory(self, memory_id: int) -> int:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                "DELETE FROM long_term_memories WHERE id = %s RETURNING id",
                (memory_id,),
            ).fetchone()
        return 1 if row else 0

    def clear_memories(self, character_id: Optional[str] = None) -> int:
        self._ensure_database()
        with self._connect() as connection:
            if character_id:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM long_term_memories WHERE character_id = %s",
                    (character_id,),
                ).fetchone()
                deleted = int(row["count"]) if row else 0
                connection.execute(
                    "DELETE FROM long_term_memories WHERE character_id = %s",
                    (character_id,),
                )
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM long_term_memories"
                ).fetchone()
                deleted = int(row["count"]) if row else 0
                connection.execute("DELETE FROM long_term_memories")
        return deleted

    def save_feedback(self, *, turn_id: int, score: int, note: str) -> Dict[str, Any]:
        self._ensure_database()
        now = _now()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    INSERT INTO turn_feedback (turn_id, score, note, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (turn_id, score, note, now),
                ).fetchone()
        except psycopg.errors.ForeignKeyViolation as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Turn {turn_id} does not exist.",
            ) from exc
        return {
            "id": row["id"],
            "turn_id": row["turn_id"],
            "score": row["score"],
            "note": row["note"],
            "created_at": self._as_text(row["created_at"]),
        }

    def export_data(self) -> Dict[str, Any]:
        self._ensure_database()
        with self._connect() as connection:
            sessions = connection.execute(
                "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
            ).fetchall()
            turns = connection.execute(
                "SELECT * FROM chat_turns ORDER BY id ASC"
            ).fetchall()
            memories = connection.execute(
                "SELECT * FROM long_term_memories ORDER BY id ASC"
            ).fetchall()
            feedback = connection.execute(
                "SELECT * FROM turn_feedback ORDER BY id ASC"
            ).fetchall()
            knowledge = connection.execute(
                "SELECT * FROM knowledge_items ORDER BY id ASC"
            ).fetchall()

        return {
            "exported_at": _now(),
            "sessions": [self._plain_row(row) for row in sessions],
            "turns": [self._plain_row(row) for row in turns],
            "memories": [self._plain_row(row) for row in memories],
            "knowledge": [self._plain_row(row) for row in knowledge],
            "feedback": [self._plain_row(row) for row in feedback],
        }

    def create_knowledge(
        self,
        *,
        character_id: str,
        source_type: str,
        title: str,
        content: str,
        tags: List[str],
    ) -> KnowledgeRecord:
        self._ensure_database()
        now = _now()
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO knowledge_items (
                    character_id,
                    source_type,
                    title,
                    content,
                    tags_json,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (character_id, source_type, title, content, Json(tags), now, now),
            ).fetchone()
        return self._row_to_knowledge(row)

    def list_knowledge(
        self,
        *,
        character_id: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 200,
    ) -> List[KnowledgeRecord]:
        self._ensure_database()
        safe_limit = max(1, min(limit, 1000))
        clauses = []
        params: List[Any] = []
        if character_id:
            clauses.append("character_id = %s")
            params.append(character_id)
        if source_type:
            clauses.append("source_type = %s")
            params.append(source_type)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(safe_limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM knowledge_items
                {where}
                ORDER BY updated_at DESC, id DESC
                LIMIT %s
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_knowledge(row) for row in rows]

    def retrieve_knowledge(
        self,
        *,
        character_id: str,
        source_type: str,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []

        items = self.list_knowledge(
            character_id=character_id,
            source_type=source_type,
            limit=500,
        )
        scored = []
        for index, item in enumerate(items):
            text = " ".join([item.title, item.content, " ".join(item.tags)])
            score = self._score(text, query)
            scored.append((score, index, item))

        positive = [item for item in scored if item[0] > 0]
        chosen = positive if positive else scored
        chosen = sorted(chosen, key=lambda item: (-item[0], item[1]))[:limit]

        hits: List[Dict[str, Any]] = []
        for score, _, item in chosen:
            hits.append(
                {
                    "id": f"kb_{item.id}",
                    "source": f"db_{source_type}",
                    "score": score,
                    "text": item.content,
                    "payload": {
                        "id": item.id,
                        "title": item.title,
                        "content": item.content,
                        "tags": item.tags,
                        "source_type": item.source_type,
                    },
                }
            )
        return hits

    def delete_knowledge(self, item_id: int) -> int:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                "DELETE FROM knowledge_items WHERE id = %s RETURNING id",
                (item_id,),
            ).fetchone()
        return 1 if row else 0

    def clear_knowledge(
        self,
        *,
        character_id: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> int:
        self._ensure_database()
        clauses = []
        params: List[Any] = []
        if character_id:
            clauses.append("character_id = %s")
            params.append(character_id)
        if source_type:
            clauses.append("source_type = %s")
            params.append(source_type)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM knowledge_items {where}",
                tuple(params),
            ).fetchone()
            deleted = int(row["count"]) if row else 0
            connection.execute(
                f"DELETE FROM knowledge_items {where}",
                tuple(params),
            )
        return deleted

    def import_jsonl_knowledge(self, data_dir: Path, character_id: str) -> Dict[str, int]:
        self._ensure_database()
        jobs = [
            ("lore", data_dir / "lore" / f"{character_id}_lore.jsonl"),
            ("dialogue", data_dir / "dialogues" / f"{character_id}_dialogues.jsonl"),
            ("reaction", data_dir / "reactions" / f"{character_id}_reactions.jsonl"),
        ]
        inserted = 0
        skipped = 0
        for source_type, path in jobs:
            if not path.exists():
                continue
            for item in self._read_jsonl(path):
                title, content, tags = self._knowledge_payload(source_type, item)
                if not content:
                    skipped += 1
                    continue
                if self._knowledge_exists(character_id, source_type, title, content):
                    skipped += 1
                    continue
                self.create_knowledge(
                    character_id=character_id,
                    source_type=source_type,
                    title=title,
                    content=content,
                    tags=tags,
                )
                inserted += 1
        return {"inserted": inserted, "skipped": skipped}

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _ensure_database(self) -> None:
        if self._initialized:
            return
        try:
            self._init_database()
        except psycopg.OperationalError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"PostgreSQL is not ready: {exc}",
            ) from exc
        self._initialized = True

    def _init_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_turns (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    character_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    reply TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    candidates_json JSONB NOT NULL,
                    debug_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_turns_session_id
                ON chat_turns(session_id, id)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id BIGSERIAL PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL DEFAULT 'note',
                    content TEXT NOT NULL,
                    importance INTEGER NOT NULL DEFAULT 5,
                    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    last_used_at TIMESTAMPTZ
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS turn_feedback (
                    id BIGSERIAL PRIMARY KEY,
                    turn_id BIGINT NOT NULL REFERENCES chat_turns(id) ON DELETE CASCADE,
                    score INTEGER NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_turn_feedback_turn_id
                ON turn_feedback(turn_id, created_at DESC)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id BIGSERIAL PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_knowledge_items_character_type
                ON knowledge_items(character_id, source_type, updated_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_long_term_memories_character
                ON long_term_memories(character_id, importance DESC, updated_at DESC)
                """
            )

    def _row_to_turn(self, row: Dict[str, Any]) -> ChatTurnRecord:
        candidates = [
            CandidateReply(**candidate)
            for candidate in self._ensure_json(row["candidates_json"], [])
            if isinstance(candidate, dict)
        ]
        debug = self._ensure_json(row["debug_json"], {})
        return ChatTurnRecord(
            id=row["id"],
            session_id=row["session_id"],
            character_id=row["character_id"],
            user_message=row["user_message"],
            reply=row["reply"],
            emotion=row["emotion"],
            candidates=candidates,
            debug=debug if isinstance(debug, dict) else {},
            created_at=self._as_text(row["created_at"]),
        )

    def _row_to_memory(self, row: Dict[str, Any]) -> MemoryRecord:
        tags = self._ensure_json(row["tags_json"], [])
        return MemoryRecord(
            id=row["id"],
            character_id=row["character_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            importance=row["importance"],
            tags=tags if isinstance(tags, list) else [],
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
            last_used_at=self._as_text(row["last_used_at"]) if row["last_used_at"] else None,
        )

    def _row_to_knowledge(self, row: Dict[str, Any]) -> KnowledgeRecord:
        tags = self._ensure_json(row["tags_json"], [])
        return KnowledgeRecord(
            id=row["id"],
            character_id=row["character_id"],
            source_type=row["source_type"],
            title=row["title"],
            content=row["content"],
            tags=tags if isinstance(tags, list) else [],
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
        )

    def _knowledge_exists(
        self,
        character_id: str,
        source_type: str,
        title: str,
        content: str,
    ) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id
                FROM knowledge_items
                WHERE character_id = %s
                  AND source_type = %s
                  AND title = %s
                  AND content = %s
                LIMIT 1
                """,
                (character_id, source_type, title, content),
            ).fetchone()
        return row is not None

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    items.append(value)
        return items

    def _knowledge_payload(
        self,
        source_type: str,
        item: Dict[str, Any],
    ) -> tuple[str, str, List[str]]:
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        if source_type == "lore":
            return (
                str(item.get("title", "")),
                str(item.get("content", "")),
                [str(tag) for tag in tags],
            )
        if source_type == "dialogue":
            title = str(item.get("scene", "") or item.get("id", ""))
            parts = [
                item.get("style_summary", ""),
                item.get("rewrite_rule", ""),
                item.get("emotion", ""),
                item.get("intent", ""),
            ]
            return title, "；".join(str(part) for part in parts if part), [str(tag) for tag in tags]

        title = str(item.get("situation", "") or item.get("id", ""))
        parts = [
            item.get("reaction", ""),
            item.get("reply_pattern", ""),
            item.get("avoid", ""),
        ]
        return title, "；".join(str(part) for part in parts if part), [str(tag) for tag in tags]

    def _ensure_json(self, value: Any, fallback: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return fallback
        return value if value is not None else fallback

    def _plain_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def _masked_database_url(self) -> str:
        parts = urlsplit(self.database_url)
        if "@" not in parts.netloc:
            return self.database_url
        user_info, host_info = parts.netloc.rsplit("@", 1)
        username = user_info.split(":", 1)[0]
        netloc = f"{username}:***@{host_info}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    def _as_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _score(self, text: str, query: str) -> int:
        haystack = text.lower()
        terms = self._terms(query)
        score = 0
        for term in terms:
            if term in haystack:
                score += len(term) + haystack.count(term)
        return score

    def _terms(self, text: str) -> List[str]:
        normalized = text.lower().strip()
        chunks = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", normalized)
        terms = set()
        for chunk in chunks:
            if len(chunk) <= 1:
                continue
            terms.add(chunk)
            if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
                for size in (2, 3, 4):
                    for index in range(0, max(len(chunk) - size + 1, 0)):
                        terms.add(chunk[index : index + size])
        return sorted(terms, key=lambda item: (-len(item), item))


database_service = DatabaseService(settings.database_url)
