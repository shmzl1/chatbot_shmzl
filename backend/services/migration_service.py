"""Retired migration-service compatibility module.

Default startup runs SQLite migrations through sqlite_migration_service.
"""

from fastapi import HTTPException


class MigrationService:
    def run_migrations(self, *_args, **_kwargs) -> None:
        raise HTTPException(
            status_code=500,
            detail=(
                "This migration service is retired. Use SQLite migrations from "
                "backend/database/sqlite_migrations for startup."
            ),
        )


migration_service = MigrationService()
