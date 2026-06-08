# Diary Module

`diary` is an independent feature domain reserved for future diary writing and
diary-reading conversations. It is intentionally not included in
`backend/main.py` yet and exposes no endpoints in this migration.

## Future Responsibility

- Let the user write diary entries.
- Let the user choose a character.
- Let the user select diary entries for the character to read.
- Let the character participate in a conversation after reading.
- Let different characters respond according to their own persona.

## Data Boundary

- `diary` will use its own tables, such as `diary_entries`,
  `diary_reading_sessions`, and `diary_reading_turns`.
- `diary` must not write to `chat_sessions` or `chat_turns`.
- `diary` must not depend on `schedule`.
- `diary` may write durable user-understanding signals through
  `relationship_memory`.
- `diary` may read `relationship_memory` when generating character replies.

