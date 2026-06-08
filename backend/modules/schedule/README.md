# Schedule Module

## Module Responsibility

Reserved module for future schedule planning, schedule items, reviews, and
schedule feedback.

## Not Responsible For

Currently no business implementation. It does not own chat sessions, diary
entries, or character packs.

## Future Public Interfaces

Future routes may support creating plans, editing items, reviewing completion,
and generating character feedback.

## Data Boundary

Future tables may include `schedule_plans`, `schedule_items`, and
`schedule_reviews`. This module must not write to `chat_sessions` or
`chat_turns`.

## Allowed Dependencies

May read characters through the characters module and later share insights
through `relationship_memory`.

## Forbidden Dependencies

Must not import diary repositories. Must not store schedule data as chat turns.

## Codex Notes

This module is placeholder-only. Do not implement schedule business logic unless
the user explicitly asks.

