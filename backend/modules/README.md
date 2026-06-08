# Backend Modules

`backend/modules` is the feature-oriented entry point for new backend code.
The legacy `backend/api` and `backend/services` packages remain in place while
the project migrates gradually.

## Current Migration Pattern

Existing features use thin wrapper modules first. For example,
`modules.chat.api` imports and exposes the existing `api.chat_api.router`.
This keeps public paths stable while giving new work a clearer home.

## Dependency Rules

1. `chat`, `schedule`, and `diary` are peer feature domains.
2. `chat` must not import `schedule`.
3. `chat` must not import `diary`.
4. `schedule` must not import `chat.repository`.
5. `diary` must not import `chat.repository`.
6. `schedule` must not import `diary`.
7. `diary` must not import `schedule`.
8. `schedule` and `diary` must not write to `chat_sessions` or `chat_turns`.
9. `chat` must not write to future `schedule` or `diary` business tables.
10. All three domains may read character packs through the `characters` module.
11. All three domains may use shared LLM capabilities to generate replies.
12. All three domains may share long-term understanding through `relationship_memory`.
13. New features that affect a character's understanding of the user should write
    to `relationship_memory`, not to unrelated chat tables.

## Shared Relationship Memory

Business data stays isolated by feature domain:

- `chat` owns free-chat sessions and turns.
- `schedule` will own plans, items, reviews, and schedule feedback.
- `diary` will own diary entries, reading sessions, and reading turns.

Meaningful long-term understanding can be shared through `relationship_memory`.
That layer represents what the same character has learned about the same user
across different scenarios.

