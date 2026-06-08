# Diary Module

## Module Responsibility

Reserved module for future diary entries, diary reading sessions, and
character-specific diary conversations.

## Not Responsible For

Currently no business implementation. It does not own chat sessions, schedule
plans, or character packs.

## Future Public Interfaces

Future routes may support diary entry management, selecting entries for a
character to read, and diary-reading conversations.

## Data Boundary

Future tables may include `diary_entries`, `diary_reading_sessions`, and
`diary_reading_turns`. This module must not write to `chat_sessions` or
`chat_turns`.

## Allowed Dependencies

May read characters through the characters module and later share insights
through `relationship_memory`.

## Forbidden Dependencies

Must not import schedule repositories. Must not store diary reading turns as
ordinary chat turns.

## Codex Notes

This module is placeholder-only. Do not implement diary business logic unless
the user explicitly asks.

