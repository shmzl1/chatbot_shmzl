"""Legacy PostgreSQL migration module.

The default local desktop runtime uses SQLite via sqlite_migration_service.
This module is intentionally kept free of psycopg imports so normal startup
does not depend on PostgreSQL packages.
"""

from fastapi import HTTPException


class MigrationService:
    def run_migrations(self, *_args, **_kwargs) -> None:
        raise HTTPException(
            status_code=500,
            detail=(
                "PostgreSQL migrations are legacy-only. Use SQLite migrations "
                "from backend/database/sqlite_migrations for default startup."
            ),
        )


migration_service = MigrationService()
