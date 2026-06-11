import json
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row
from psycopg.types.json import Json

from core.config import settings
from core.schemas import CandidateReply, ChatSessionSummary, ChatTurnRecord, MemoryRecord, UserRecord
from core.schemas import KnowledgeRecord
from services.migration_service import migration_service


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
            persona_feedback_row = connection.execute(
                "SELECT COUNT(*) AS count FROM persona_turn_feedback"
            ).fetchone()
            relationship_memory_row = connection.execute(
                "SELECT COUNT(*) AS count FROM relationship_memory_events"
            ).fetchone()

        return {
            "database_backend": "postgresql",
            "database_url": self._masked_database_url(),
            "session_count": int(session_row["count"]) if session_row else 0,
            "turn_count": int(turn_row["count"]) if turn_row else 0,
            "memory_count": int(memory_row["count"]) if memory_row else 0,
            "relationship_memory_count": (
                int(relationship_memory_row["count"]) if relationship_memory_row else 0
            ),
            "knowledge_count": int(knowledge_row["count"]) if knowledge_row else 0,
            "feedback_count": int(feedback_row["count"]) if feedback_row else 0,
            "persona_feedback_count": (
                int(persona_feedback_row["count"]) if persona_feedback_row else 0
            ),
        }

    def is_ready(self) -> bool:
        try:
            self._ensure_database()
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except psycopg.OperationalError:
            return False

    def ensure_ready(self) -> None:
        self._ensure_database()
        with self._connect() as connection:
            connection.execute("SELECT 1").fetchone()

    def create_user(
        self,
        *,
        username: str,
        email: Optional[str],
        password_hash: str,
    ) -> UserRecord:
        self._ensure_database()
        normalized_username = username.strip()
        normalized_email = email.strip().lower() if email else None
        now = _now()

        if self.user_count() > 0:
            raise HTTPException(status_code=409, detail="本地账号已初始化")
        if self.get_user_by_username(normalized_username):
            raise HTTPException(status_code=409, detail="用户名已存在")
        if normalized_email and self.get_user_by_email(normalized_email):
            raise HTTPException(status_code=409, detail="邮箱已存在")

        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password_hash,
                    avatar_url,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, NULL, %s, %s)
                RETURNING *
                """,
                (normalized_username, normalized_email, password_hash, now, now),
            ).fetchone()
        return self._row_to_user(row)

    def user_count(self) -> int:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        return int(row["count"]) if row else 0

    def get_user_by_username(self, username: str) -> Optional[UserRecord]:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) LIMIT 1",
                (username.strip(),),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email IS NOT NULL AND LOWER(email) = LOWER(%s) LIMIT 1",
                (email.strip(),),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[UserRecord]:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE id = %s LIMIT 1",
                (user_id,),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_single_user(self) -> Optional[UserRecord]:
        self._ensure_database()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM users ORDER BY id ASC LIMIT 2"
            ).fetchall()
        if len(rows) > 1:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Duplicate local users found. This project supports exactly one "
                    "local user; please inspect the users table and manually resolve duplicates."
                ),
            )
        return self._row_to_user(rows[0]) if rows else None

    def update_user_profile(self, user_id: int, username: str) -> UserRecord:
        self._ensure_database()
        normalized_username = username.strip()
        if not normalized_username:
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if len(normalized_username) > 50:
            raise HTTPException(status_code=400, detail="用户名长度不能超过 50")

        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        updated_at = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (normalized_username, _now(), user_id),
                ).fetchone()
        except psycopg.errors.UniqueViolation as exc:
            raise HTTPException(status_code=409, detail="用户名已存在") from exc

        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        return self._row_to_user(row)

    def update_user_avatar(self, user_id: int, avatar_url: str) -> UserRecord:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                """
                UPDATE users
                SET avatar_url = %s,
                    updated_at = %s
                WHERE id = %s
                RETURNING *
                """,
                (avatar_url, _now(), user_id),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        return self._row_to_user(row)

    def upsert_character_avatar(self, character_id: str, avatar_url: str) -> str:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO character_avatar_map (
                    character_id,
                    avatar_url,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (character_id) DO UPDATE SET
                    avatar_url = EXCLUDED.avatar_url,
                    updated_at = NOW()
                RETURNING avatar_url
                """,
                (character_id, avatar_url),
            ).fetchone()
        return str(row["avatar_url"])

    def get_character_avatar_map(self) -> Dict[str, str]:
        self._ensure_database()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT character_id, avatar_url FROM character_avatar_map"
            ).fetchall()
        return {str(row["character_id"]): str(row["avatar_url"]) for row in rows}

    def get_character_avatar(self, character_id: str) -> Optional[str]:
        self._ensure_database()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT avatar_url
                FROM character_avatar_map
                WHERE character_id = %s
                LIMIT 1
                """,
                (character_id,),
            ).fetchone()
        return str(row["avatar_url"]) if row else None

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
        is_pinned: bool = False,
        is_editable: bool = True,
        read_policy: str = "relevant",
        status: str = "active",
        expires_at: Optional[str] = None,
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
                    is_pinned,
                    is_editable,
                    read_policy,
                    status,
                    expires_at,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    character_id,
                    memory_type,
                    content,
                    importance,
                    Json(tags),
                    is_pinned,
                    is_editable,
                    read_policy,
                    status,
                    expires_at,
                    now,
                    now,
                ),
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
        self._ensure_database()
        with self._connect() as connection:
            pinned_rows = connection.execute(
                """
                SELECT *
                FROM long_term_memories
                WHERE character_id = %s
                  AND status = 'active'
                  AND (is_pinned = TRUE OR read_policy = 'always')
                  AND read_policy <> 'never'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY importance DESC, updated_at DESC, id DESC
                """,
                (character_id,),
            ).fetchall()
            normal_rows = connection.execute(
                """
                SELECT *
                FROM long_term_memories
                WHERE character_id = %s
                  AND status = 'active'
                  AND is_pinned = FALSE
                  AND read_policy = 'relevant'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY importance DESC, updated_at DESC, id DESC
                LIMIT 300
                """,
                (character_id,),
            ).fetchall()

        pinned_memories = [self._row_to_memory(row) for row in pinned_rows]
        memories = [self._row_to_memory(row) for row in normal_rows]
        scored = []
        for index, memory in enumerate(memories):
            text = " ".join([memory.content, " ".join(memory.tags), memory.memory_type])
            score = self._score(text, query) + memory.importance
            scored.append((score, index, memory))

        chosen = sorted(scored, key=lambda item: (-item[0], item[1]))[: max(0, limit)]
        hits: List[Dict[str, Any]] = []
        for memory in pinned_memories:
            hits.append(self._memory_hit(memory, memory.importance, pinned=True))
        for score, _, memory in chosen:
            hits.append(self._memory_hit(memory, score, pinned=False))
        return hits

    def _memory_hit(self, memory: MemoryRecord, score: int, *, pinned: bool) -> Dict[str, Any]:
        return {
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
                "is_pinned": memory.is_pinned,
                "read_policy": memory.read_policy,
                "status": memory.status,
                "expires_at": memory.expires_at,
                "pinned_prompt": pinned,
            },
        }

    def mark_memories_used(self, memory_ids: List[int]) -> None:
        if not memory_ids:
            return
        self._ensure_database()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE long_term_memories
                SET last_used_at = %s,
                    use_count = use_count + 1
                WHERE id = ANY(%s)
                """,
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

    def save_persona_turn_feedback(
        self,
        *,
        character_id: str,
        session_id: Optional[str],
        turn_id: Optional[int],
        user_message: str,
        assistant_message: str,
        rating: str,
        issue_tags: List[str],
        comment: str,
    ) -> Dict[str, Any]:
        self._ensure_database()
        now = _now()
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO persona_turn_feedback (
                    character_id,
                    session_id,
                    turn_id,
                    user_message,
                    assistant_message,
                    rating,
                    issue_tags_json,
                    comment,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    character_id,
                    session_id,
                    turn_id,
                    user_message,
                    assistant_message,
                    rating,
                    Json(issue_tags),
                    comment,
                    now,
                ),
            ).fetchone()
        return self._row_to_persona_feedback(row)

    def persona_feedback_summary(
        self,
        *,
        character_id: str,
        limit: int = 30,
    ) -> Dict[str, Any]:
        feedback = self.list_persona_feedback(character_id=character_id, limit=limit)
        all_feedback = self.list_persona_feedback(character_id=character_id, limit=500)
        rating_counts = Counter(item["rating"] for item in all_feedback)
        tag_counts: Counter[str] = Counter()
        for item in all_feedback:
            tag_counts.update(str(tag) for tag in item["issue_tags"])

        return {
            "character_id": character_id,
            "total_feedback": len(all_feedback),
            "rating_counts": {
                "good": rating_counts.get("good", 0),
                "bad": rating_counts.get("bad", 0),
                "neutral": rating_counts.get("neutral", 0),
            },
            "issue_tag_counts": dict(tag_counts.most_common()),
            "top_issues": [
                {"tag": tag, "count": count}
                for tag, count in tag_counts.most_common(5)
            ],
            "recent_feedback": feedback,
        }

    def list_persona_feedback(
        self,
        *,
        character_id: str,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        self._ensure_database()
        safe_limit = max(1, min(limit, 500))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM persona_turn_feedback
                WHERE character_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (character_id, safe_limit),
            ).fetchall()
        return [self._row_to_persona_feedback(row) for row in rows]

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
            persona_feedback = connection.execute(
                "SELECT * FROM persona_turn_feedback ORDER BY id ASC"
            ).fetchall()
            relationship_memory = connection.execute(
                "SELECT * FROM relationship_memory_events ORDER BY id ASC"
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
            "persona_feedback": [self._plain_row(row) for row in persona_feedback],
            "relationship_memory": [self._plain_row(row) for row in relationship_memory],
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
                raise HTTPException(
                    status_code=500,
                    detail=f"Knowledge JSONL file is missing: {path}",
                )
            for item in self._read_jsonl(path):
                title, content, tags = self._knowledge_payload(source_type, item)
                if not content:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Knowledge JSONL item in {path} has empty content.",
                    )
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
                detail=f"Database connection failed before migration: {exc}",
            ) from exc
        self._initialized = True

    def _init_database(self) -> None:
        migration_service.run_migrations(self._connect)

    def _row_to_turn(self, row: Dict[str, Any]) -> ChatTurnRecord:
        candidates_json = self._ensure_json(row["candidates_json"], "chat_turns.candidates_json")
        if not isinstance(candidates_json, list):
            raise HTTPException(
                status_code=500,
                detail=f"chat_turns.candidates_json for turn {row['id']} must be a list.",
            )
        candidates = []
        for candidate in candidates_json:
            if not isinstance(candidate, dict):
                raise HTTPException(
                    status_code=500,
                    detail=f"chat_turns.candidates_json for turn {row['id']} contains a non-object item.",
                )
            candidates.append(CandidateReply(**candidate))
        debug = self._ensure_json(row["debug_json"], "chat_turns.debug_json")
        if not isinstance(debug, dict):
            raise HTTPException(
                status_code=500,
                detail=f"chat_turns.debug_json for turn {row['id']} must be an object.",
            )
        return ChatTurnRecord(
            id=row["id"],
            session_id=row["session_id"],
            character_id=row["character_id"],
            user_message=row["user_message"],
            reply=row["reply"],
            emotion=row["emotion"],
            candidates=candidates,
            debug=debug,
            created_at=self._as_text(row["created_at"]),
        )

    def _row_to_memory(self, row: Dict[str, Any]) -> MemoryRecord:
        tags = self._ensure_json(row["tags_json"], "long_term_memories.tags_json")
        if not isinstance(tags, list):
            raise HTTPException(
                status_code=500,
                detail=f"long_term_memories.tags_json for memory {row['id']} must be a list.",
            )
        return MemoryRecord(
            id=row["id"],
            character_id=row["character_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            importance=row["importance"],
            tags=tags,
            is_pinned=bool(row.get("is_pinned", False)),
            is_editable=bool(row.get("is_editable", True)),
            read_policy=str(row.get("read_policy") or "relevant"),
            status=str(row.get("status") or "active"),
            expires_at=self._as_text(row["expires_at"]) if row.get("expires_at") else None,
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
            last_used_at=self._as_text(row["last_used_at"]) if row["last_used_at"] else None,
            use_count=int(row.get("use_count") or 0),
        )

    def _row_to_knowledge(self, row: Dict[str, Any]) -> KnowledgeRecord:
        tags = self._ensure_json(row["tags_json"], "knowledge_items.tags_json")
        if not isinstance(tags, list):
            raise HTTPException(
                status_code=500,
                detail=f"knowledge_items.tags_json for item {row['id']} must be a list.",
            )
        return KnowledgeRecord(
            id=row["id"],
            character_id=row["character_id"],
            source_type=row["source_type"],
            title=row["title"],
            content=row["content"],
            tags=tags,
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
        )

    def _row_to_user(self, row: Dict[str, Any]) -> UserRecord:
        return UserRecord(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            avatar_url=row["avatar_url"],
            created_at=self._as_text(row["created_at"]),
            updated_at=self._as_text(row["updated_at"]),
        )

    def _row_to_persona_feedback(self, row: Dict[str, Any]) -> Dict[str, Any]:
        tags = self._ensure_json(
            row["issue_tags_json"],
            "persona_turn_feedback.issue_tags_json",
        )
        if not isinstance(tags, list):
            raise HTTPException(
                status_code=500,
                detail=f"persona_turn_feedback.issue_tags_json for feedback {row['id']} must be a list.",
            )
        return {
            "id": row["id"],
            "character_id": row["character_id"],
            "session_id": row["session_id"],
            "turn_id": row["turn_id"],
            "user_message": row["user_message"],
            "assistant_message": row["assistant_message"],
            "rating": row["rating"],
            "issue_tags": [str(tag) for tag in tags],
            "comment": row["comment"],
            "created_at": self._as_text(row["created_at"]),
        }

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
                except json.JSONDecodeError as exc:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid JSONL in {path} at line {line_no}: {exc}",
                    ) from exc
                if not isinstance(value, dict):
                    raise HTTPException(
                        status_code=500,
                        detail=f"JSONL item in {path} at line {line_no} must be an object.",
                    )
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

    def _ensure_json(self, value: Any, field_name: str) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid JSON stored in {field_name}: {exc}",
                ) from exc
        if value is None:
            raise HTTPException(
                status_code=500,
                detail=f"Required JSON value is NULL: {field_name}",
            )
        return value

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
