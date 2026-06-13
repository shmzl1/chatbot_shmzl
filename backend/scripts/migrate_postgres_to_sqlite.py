import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.sqlite_migration_service import sqlite_migration_service  # noqa: E402


TABLES: list[tuple[str, list[str]]] = [
    (
        "users",
        ["id", "username", "email", "password_hash", "avatar_url", "created_at", "updated_at"],
    ),
    (
        "chat_sessions",
        ["id", "character_id", "user_id", "created_at", "updated_at"],
    ),
    (
        "chat_turns",
        [
            "id",
            "session_id",
            "character_id",
            "user_message",
            "reply",
            "emotion",
            "candidates_json",
            "debug_json",
            "created_at",
        ],
    ),
    (
        "long_term_memories",
        [
            "id",
            "character_id",
            "memory_type",
            "content",
            "importance",
            "tags_json",
            "is_pinned",
            "is_editable",
            "read_policy",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
            "last_used_at",
            "use_count",
        ],
    ),
    ("turn_feedback", ["id", "turn_id", "score", "note", "created_at"]),
    (
        "persona_turn_feedback",
        [
            "id",
            "character_id",
            "session_id",
            "turn_id",
            "user_message",
            "assistant_message",
            "rating",
            "issue_tags_json",
            "comment",
            "created_at",
        ],
    ),
    (
        "relationship_memory_events",
        [
            "id",
            "character_id",
            "source_type",
            "source_id",
            "source_turn_id",
            "memory_type",
            "content",
            "evidence",
            "importance",
            "is_active",
            "is_pinned",
            "is_editable",
            "read_policy",
            "status",
            "expires_at",
            "last_used_at",
            "use_count",
            "created_at",
            "updated_at",
        ],
    ),
    (
        "knowledge_items",
        ["id", "character_id", "source_type", "title", "content", "tags_json", "created_at", "updated_at"],
    ),
    ("character_avatar_map", ["character_id", "avatar_url", "created_at", "updated_at"]),
    (
        "diary_entries",
        [
            "id",
            "user_id",
            "title",
            "content_markdown",
            "entry_date",
            "mood",
            "tags_json",
            "is_deleted",
            "created_at",
            "updated_at",
            "deleted_at",
        ],
    ),
    (
        "diary_attachments",
        [
            "id",
            "entry_id",
            "user_id",
            "filename",
            "original_filename",
            "content_type",
            "file_size",
            "storage_path",
            "public_url",
            "is_deleted",
            "created_at",
            "deleted_at",
        ],
    ),
]

JSON_FIELDS = {"candidates_json", "debug_json", "tags_json", "issue_tags_json", "evidence"}
BOOL_FIELDS = {"is_pinned", "is_editable", "is_active", "is_deleted"}


def import_psycopg():
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "迁移脚本需要可选依赖 psycopg。请先执行：pip install 'psycopg[binary]'"
        ) from exc
    return psycopg, dict_row


def sqlite_connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def backup_sqlite(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def target_has_data(connection: sqlite3.Connection) -> bool:
    for table, _columns in TABLES:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        if row and int(row["count"]) > 0:
            return True
    return False


def pg_table_columns(pg_connection: Any, table: str) -> set[str]:
    rows = pg_connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        """,
        (table,),
    ).fetchall()
    return {str(row["column_name"]) for row in rows}


def normalize_value(column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in JSON_FIELDS:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    if column in BOOL_FIELDS:
        return 1 if bool(value) else 0
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def migrate_table(pg_connection: Any, sqlite_connection: sqlite3.Connection, table: str, columns: list[str]) -> int:
    source_columns = pg_table_columns(pg_connection, table)
    if not source_columns:
        raise RuntimeError(f"旧 PostgreSQL 数据库缺少业务表：{table}")
    selected_columns = [column for column in columns if column in source_columns]
    missing_columns = [column for column in columns if column not in source_columns]
    if missing_columns:
        print(f"[warn] {table} 缺少字段，将使用 SQLite 默认值：{', '.join(missing_columns)}")

    select_sql = f"SELECT {', '.join(selected_columns)} FROM {table} ORDER BY 1"
    rows = pg_connection.execute(select_sql).fetchall()
    if not rows:
        return 0

    placeholders = ", ".join("?" for _ in selected_columns)
    insert_sql = f"INSERT INTO {table} ({', '.join(selected_columns)}) VALUES ({placeholders})"
    for row in rows:
        values = [normalize_value(column, row[column]) for column in selected_columns]
        sqlite_connection.execute(insert_sql, values)
    return len(rows)


def run(postgres_url: str, sqlite_path: Path, overwrite: bool) -> None:
    psycopg, dict_row = import_psycopg()
    backup_path = backup_sqlite(sqlite_path)
    if backup_path:
        print(f"已备份现有 SQLite 文件：{backup_path}")
    if overwrite and sqlite_path.exists():
        sqlite_path.unlink()

    with sqlite_connect(sqlite_path) as sqlite_connection:
        sqlite_migration_service.run_migrations(sqlite_connection)
        if target_has_data(sqlite_connection) and not overwrite:
            raise SystemExit(
                "目标 SQLite 已有数据。请先备份，或确认后加 --overwrite。"
            )
        sqlite_connection.execute("PRAGMA foreign_keys = OFF")
        with psycopg.connect(postgres_url, row_factory=dict_row) as pg_connection:
            stats: dict[str, int] = {}
            for table, columns in TABLES:
                count = migrate_table(pg_connection, sqlite_connection, table, columns)
                stats[table] = count
                print(f"{table}: {count}")
        sqlite_connection.commit()
        sqlite_connection.execute("PRAGMA foreign_keys = ON")
        violations = sqlite_connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            details = "; ".join(str(dict(row)) for row in violations[:10])
            raise RuntimeError(f"SQLite 外键校验失败：{details}")

    print(f"迁移完成：{sqlite_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy PostgreSQL data to local SQLite.")
    parser.add_argument("--postgres-url", required=True)
    parser.add_argument("--sqlite-path", default=str(BACKEND_DIR / "data" / "chatbot.db"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    run(
        postgres_url=args.postgres_url,
        sqlite_path=Path(args.sqlite_path),
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
