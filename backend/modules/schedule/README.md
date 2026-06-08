# Schedule Module

`schedule` is an independent feature domain reserved for future schedule
planning and review. It is intentionally not included in `backend/main.py` yet
and exposes no endpoints in this migration.

## Future Responsibility

- Let the user choose a character.
- Let the user enter what they need to do today.
- Let the character help arrange time.
- Let the user manually adjust planned times.
- Let the character respond to the adjusted plan according to persona.
- Let the user report completed and unfinished items at night.
- Let the character encourage, tease, criticize, or summarize according to
  persona and the review result.

## Data Boundary

- `schedule` will use its own tables, such as `schedule_plans`,
  `schedule_items`, `schedule_reviews`, and `schedule_feedback_turns`.
- `schedule` must not write to `chat_sessions` or `chat_turns`.
- `schedule` must not depend on `diary`.
- `schedule` may write durable user-understanding signals through
  `relationship_memory`.
- `schedule` may read `relationship_memory` when generating character feedback.

