# Backend Modules

`backend/modules` is the backend feature boundary for the virtual-character
companion system. New backend work should start here instead of adding more
logic to legacy flat packages.

## Module List

- `auth`: local single-user login lock, token issuance, current-user lookup.
- `chat`: ordinary character chat flow.
- `characters`: character packs, character templates, avatars, validation, CLI-facing character management.
- `persona_review`: persona feedback, persona editor discussion, preview, apply, and rollback flow.
- `memory`: long-term memory records used by chat.
- `knowledge`: knowledge items and retrieval support.
- `voice`: GPT-SoVITS-facing voice synthesis.
- `relationship_memory`: future shared character-understanding layer across scenarios.
- `schedule`: reserved module for future schedule management.
- `diary`: reserved module for future diary reading and diary conversations.
- `debug`: local development/debug endpoints.
- `health`: lightweight health checks.

## File Roles

- `api.py`: HTTP boundary only. Parse requests, call services, return responses.
- `service.py`: business logic and orchestration.
- `repository.py`: database or filesystem persistence boundary.
- `schemas.py`: module-specific request/response models.
- `README.md`: ownership, dependency rules, data boundary, and Codex guidance.

## Dependency Rules

- Modules must not casually import another module's `repository.py`.
- Cross-module calls should use the other module's public `service.py` API.
- Shared utilities belong in `core` or a future shared module, not in an unrelated feature module.
- Do not keep adding feature-specific SQL to one large shared service.
- New features should get their own `backend/modules/{feature}` directory.
- A bug in one module should usually be fixed in that module only.
- Do not restore mock fallbacks or silent defaults.

## Chat, Schedule, Diary

`chat`, `schedule`, and `diary` are peer business domains.

- `chat` owns ordinary chat sessions and turns.
- `schedule` will own schedule plans, items, reviews, and schedule feedback.
- `diary` will own diary entries, reading sessions, and reading turns.

They do not share business conversation tables. Future `schedule` and `diary`
code must not write to `chat_sessions` or `chat_turns`.

The three domains may share durable character understanding through
`relationship_memory`, so the same character can carry understanding of the user
across different scenarios without mixing business data.

## Character Access

Character data is owned only by `characters`.

Other modules should not build paths under `backend/modules/characters/packs`
themselves. Use the public characters service or loader/writer helpers.

## Adding A Module

Copy `backend/modules/MODULE_TEMPLATE.md` into the new module README and fill in
the boundaries before adding business logic.
