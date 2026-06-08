# Persona Review Module

## Module Responsibility

Persona feedback and persona editor flow: save per-turn feedback, discuss
revision direction, generate preview JSON, apply confirmed changes, and rollback
the previous version.

## Not Responsible For

Ordinary chat, schedule, diary, permanent character deletion, or direct
character-pack path construction outside the characters module.

## Public Interfaces

- `/feedback/persona...` routes
- `POST /characters/{character_id}/persona-review/chat`
- `POST /characters/{character_id}/persona-review/finalize`
- `POST /characters/{character_id}/persona-review/apply`
- `POST /characters/{character_id}/persona-review/rollback`

## Data Boundary

Reads feedback from PostgreSQL. Reads/writes character packs only through the
characters module. `finalize` returns a preview; only `apply` writes files after
user confirmation.

## Allowed Dependencies

May call the characters service/pack writer, database access, and LLM service.

## Forbidden Dependencies

Must not write ordinary chat sessions for editor discussion. Must not bypass
characters validation. Must not modify protected character fields.

## Codex Notes

When editing persona review, verify chat/finalize/apply/rollback separation.
Never make chat or finalize write `character.json`.

