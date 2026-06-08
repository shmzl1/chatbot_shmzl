# Knowledge Module

## Module Responsibility

Knowledge item creation, listing, deletion, and retrieval support for character
responses.

## Not Responsible For

Character-pack ownership, chat session ownership, memories, schedule, diary, or
persona-review writes.

## Public Interfaces

- `/knowledge...` routes
- Retrieval support used by chat

## Data Boundary

Owns knowledge records in PostgreSQL. Character pack lore/dialogue/reaction data
is owned by `characters`, not this module.

## Allowed Dependencies

May use database access, core schemas, and character IDs supplied by callers.

## Forbidden Dependencies

Must not write chat sessions. Must not read old scattered `backend/data/lore`,
`backend/data/dialogues`, or `backend/data/reactions` as primary character data.

## Codex Notes

For knowledge work, keep persistent knowledge separate from character-pack
content. Do not move character-pack data into this module.

