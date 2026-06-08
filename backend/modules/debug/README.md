# Debug Module

## Module Responsibility

Local development debug endpoints for database state, character diagnostics,
session inspection, and feedback debugging.

## Not Responsible For

Production admin features, destructive reset flows, migrations, or business
logic.

## Public Interfaces

- `GET /debug/database`
- `GET /debug/export`
- `GET /debug/characters`
- `GET /debug/characters/{character_id}`
- Session and feedback debug routes.

## Data Boundary

Reads existing data for diagnostics. Should not silently repair or delete data.

## Allowed Dependencies

May call public services from database, characters, and persona review for
diagnostic output.

## Forbidden Dependencies

Must not perform destructive cleanup. Must not run migrations outside normal
startup flow.

## Codex Notes

Debug changes should expose clearer facts, not hide errors. Keep debug output
useful for local troubleshooting.

