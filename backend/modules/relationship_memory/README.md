# Relationship Memory Module

`relationship_memory` is the shared character relationship memory layer.

It is not an ordinary chat table.
It is not a schedule table.
It is not a diary table.

It stores durable understanding that a specific character has about the user.
Future chat, schedule, and diary features may all write meaningful insights to
this layer, and may all read from it when generating character responses.

## Future Writers

- `chat`: user preferences, boundaries, emotional state, and long-term habits
  extracted from ordinary conversation.
- `schedule`: procrastination patterns, pressure sources, task habits, and
  completion review signals extracted from planning and review.
- `diary`: recent life events, loneliness, emotional changes, and concerns
  extracted from diary reading.

## Future Readers

- `chat` may read relationship memory when replying.
- `schedule` may read relationship memory when giving schedule feedback.
- `diary` may read relationship memory during diary-reading conversations.

## Future Table Sketch

Do not create this table in this migration. A future migration may add:

`relationship_memory_events`

Suggested fields:

- `id`
- `character_id`
- `source_type`: `chat`, `schedule`, or `diary`
- `source_id`
- `source_turn_id`
- `memory_type`: `user_preference`, `habit`, `emotional_state`, `life_event`,
  `boundary`, or `task_pattern`
- `content`
- `evidence`
- `importance`
- `created_at`
- `updated_at`
- `is_active`

