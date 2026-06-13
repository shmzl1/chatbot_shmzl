import re
import sqlite3
from pathlib import Path

from fastapi import HTTPException


SQLITE_MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "database" / "sqlite_migrations"


class SQLiteMigrationService:
    def run_migrations(self, connection: sqlite3.Connection) -> None:
        self._ensure_schema_table(connection)
        applied = self._applied_versions(connection)
        migration_files = sorted(SQLITE_MIGRATIONS_DIR.glob("*.sql"))
        if not migration_files:
            raise HTTPException(
                status_code=500,
                detail=f"No SQLite migration files found in {SQLITE_MIGRATIONS_DIR}",
            )

        for migration_file in migration_files:
            version, name = self._parse_migration_name(migration_file)
            if version in applied:
                continue
            sql = migration_file.read_text(encoding="utf-8")
            self._validate_sql(migration_file, sql)
            try:
                connection.executescript(sql)
                connection.execute(
                    """
                    INSERT INTO schema_migrations (version, name, applied_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (version, name),
                )
                connection.commit()
            except sqlite3.Error as exc:
                connection.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"SQLite migration failed in {migration_file.name}: {exc}",
                ) from exc

    def _ensure_schema_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        connection.commit()

    def _applied_versions(self, connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
        return {str(row["version"]) for row in rows}

    def _parse_migration_name(self, migration_file: Path) -> tuple[str, str]:
        match = re.fullmatch(r"(\d+)_(.+)\.sql", migration_file.name)
        if not match:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid SQLite migration filename: {migration_file.name}",
            )
        return match.group(1), match.group(2)

    def _validate_sql(self, migration_file: Path, sql: str) -> None:
        forbidden = ("DROP DATABASE", "DROP SCHEMA")
        upper_sql = sql.upper()
        for token in forbidden:
            if token in upper_sql:
                raise HTTPException(
                    status_code=500,
                    detail=f"Forbidden destructive SQL in SQLite migration {migration_file.name}: {token}",
                )


sqlite_migration_service = SQLiteMigrationService()
