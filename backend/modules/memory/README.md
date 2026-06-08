# Memory Module

## Module Responsibility

Long-term memory records used by ordinary chat.

## Not Responsible For

Future cross-scenario `relationship_memory`, character packs, knowledge items,
schedule plans, or diary entries.

## Public Interfaces

- `/memory...` routes
- Memory suggestion support used by chat

## Data Boundary

Owns current long-term memory records in PostgreSQL.

## Allowed Dependencies

May use database access, core schemas, and LLM helpers where already wired.

## Forbidden Dependencies

Must not write chat turns directly. Must not write schedule/diary business data.

## Codex Notes

Do not confuse current `memory` with future `relationship_memory`. If a task
asks for cross-scenario character understanding, read the relationship memory
README first.

