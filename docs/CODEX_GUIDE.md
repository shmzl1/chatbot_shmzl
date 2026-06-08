# Codex Development Guide

This guide is the first stop for AI agents working on the project.

## Project Principles

- Keep modules loosely coupled.
- Modify by feature module whenever possible.
- Do not make broad cross-module changes for a local bug.
- Do not restore mock fallbacks or silent defaults.
- Do not swallow configuration, database, character-pack, LLM, or voice errors.
- Do not run long tasks automatically.
- Do not run `git commit` or `git push` unless the user explicitly asks.

## Reading Order

Read only the smallest useful set of files first.

- Login/auth task: `backend/modules/auth/README.md`
- Ordinary chat task: `backend/modules/chat/README.md`
- Character/person task: `backend/modules/characters/README.md`
- Persona editor task: `backend/modules/persona_review/README.md`
- Memory task: `backend/modules/memory/README.md`
- Knowledge task: `backend/modules/knowledge/README.md`
- Voice task: `backend/modules/voice/README.md`
- Schedule task: `backend/modules/schedule/README.md`
- Diary task: `backend/modules/diary/README.md`
- Debug task: `backend/modules/debug/README.md`
- Architecture/refactor task: `docs/ARCHITECTURE.md` and `backend/modules/README.md`

After reading the module README, inspect only that module's `api.py`,
`service.py`, `repository.py`, and `schemas.py` as needed.

## Required Final Report

Every Codex change should report:

- Modified files.
- Why those files were changed.
- Whether the change crossed module boundaries.
- Whether database code changed.
- Whether a migration was added.
- Whether frontend code changed.
- Whether README/docs changed.
- Lightweight check results.

## Default Forbidden Commands

Do not run these unless the user explicitly requests them:

- `uvicorn main:app --reload`
- `docker compose up`
- `docker compose down`
- `docker compose down -v`
- `git commit`
- `git push`
- Long-running frontend or backend sessions

## Lightweight Checks

Preferred syntax check:

```powershell
cd E:\my_software\chatbot\backend
conda activate 3-chatbot
python -m compileall .
```

If `compileall` cannot write to existing `__pycache__`, use a temporary pycache
prefix and report that detail.

