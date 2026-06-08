# Architecture

## Overview

```text
frontend/simple_web
  -> backend FastAPI
  -> backend/modules/*
  -> PostgreSQL / character-pack files / uploads / outputs
  -> OpenAI-compatible LLM
  -> optional GPT-SoVITS
```

The project is a local virtual-character companion system. The backend is a
FastAPI app composed of feature modules under `backend/modules`.

## Backend Layering

Inside each module:

```text
api.py -> service.py -> repository.py
schemas.py describes request/response models
```

Rules:

- `api.py` handles HTTP details only.
- `service.py` owns business logic and orchestration.
- `repository.py` owns persistence, whether database or filesystem.
- `schemas.py` owns module-specific request/response models.
- Cross-module callers should use public services, not another module's repository.

## Character System

Characters are owned by `backend/modules/characters`.

Character data lives only at:

```text
backend/modules/characters/packs/{character_id}/character.json
```

Templates live at:

```text
backend/modules/characters/templates/
```

Other modules must not construct character-pack paths themselves. They should
use `modules.characters.service`, `pack_loader`, `pack_writer`, or `repository`.

## Persona Review

Persona review reads characters through the characters module.

- `chat` only discusses revision direction.
- `finalize` only returns a final plan and `preview_character_json`.
- `apply` writes `character.json` after user confirmation.
- `apply` backs up the previous version first.
- `rollback` restores the previous backup.

## Relationship Memory Design

`relationship_memory` is the future shared layer for durable understanding of
the user by the same character.

`chat`, `schedule`, and `diary` are separate business domains. They must not
share business conversation tables. They may later share selected long-term
insights through `relationship_memory`.

## Error Exposure

Configuration errors, database errors, character-pack errors, LLM errors, and
voice errors should be explicit. Do not silently fall back to mock data or
pretend success.

Frontend code should surface backend `detail` whenever possible.
