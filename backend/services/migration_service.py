import re
from pathlib import Path
from typing import Callable

import psycopg
from fastapi import HTTPException


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "database" / "migrations"
FORBIDDEN_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\s+chat_sessions\b",
    r"\bDELETE\s+FROM\s+chat_turns\b",
    r"\bDELETE\s+FROM\s+long_term_memories\b",
    r"\bDELETE\s+FROM\s+knowledge_items\b",
]


class MigrationService:
    def run_migrations(self, connect: Callable[[], psycopg.Connection]) -> None:
        if not MIGRATIONS_DIR.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Migration directory does not exist: {MIGRATIONS_DIR}",
            )

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not migration_files:
            raise HTTPException(
                status_code=500,
                detail=f"No migration files found in {MIGRATIONS_DIR}",
            )

        with connect() as connection:
            self._ensure_schema_table(connection)
            applied = self._applied_versions(connection)

            for migration_file in migration_files:
                version, name = self._parse_migration_name(migration_file)
                if version in applied:
                    continue
                sql = migration_file.read_text(encoding="utf-8")
                self._validate_sql(migration_file, sql)
                try:
                    connection.execute(sql)
                    connection.execute(
                        """
                        INSERT INTO schema_migrations (version, name, applied_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (version) DO NOTHING
                        """,
                        (version, name),
                    )
                except psycopg.Error as exc:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"Migration failed in {migration_file.name}: "
                            f"{exc.__class__.__name__}: {exc}"
                        ),
                    ) from exc

    def _ensure_schema_table(self, connection: psycopg.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    def _applied_versions(self, connection: psycopg.Connection) -> set[str]:
        rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
        return {str(row["version"]) for row in rows}

    def _parse_migration_name(self, migration_file: Path) -> tuple[str, str]:
        match = re.fullmatch(r"(\d+)_(.+)\.sql", migration_file.name)
        if not match:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid migration filename: {migration_file.name}",
            )
        return match.group(1), match.group(2)

    def _validate_sql(self, migration_file: Path, sql: str) -> None:
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, sql, flags=re.IGNORECASE):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Forbidden destructive SQL in migration {migration_file.name}: "
                        f"{pattern}"
                    ),
                )


migration_service = MigrationService()
