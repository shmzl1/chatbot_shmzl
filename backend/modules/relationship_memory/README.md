# Relationship Memory Module

## Module Responsibility

Future shared layer for durable understanding that one character has about the
user across scenarios.

## Not Responsible For

It is not an ordinary chat table, not a schedule table, and not a diary table.
It does not currently implement persistence.

## Future Public Interfaces

- Collect insights from chat.
- Collect insights from schedule review.
- Collect insights from diary reading.
- Provide relationship context for a character.

## Data Boundary

Future table sketch: `relationship_memory_events` with `character_id`,
`source_type`, `source_id`, `memory_type`, `content`, `evidence`,
`importance`, timestamps, and active state.

## Allowed Dependencies

Future chat/schedule/diary modules may call public relationship-memory services.

## Forbidden Dependencies

Must not store complete chat, schedule, or diary business records. Must not
replace those modules' own tables.

## Codex Notes

This is a placeholder. Do not wire it into business flows or create migrations
unless the user explicitly asks.

