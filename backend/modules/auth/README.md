# Auth Module

## Module Responsibility

Local single-user login lock: setup, login, logout, current-user lookup, token
validation, and user avatar upload.

## Not Responsible For

Character data, chat sessions, persona review, memories, knowledge, or voice.

## Public Interfaces

- `/auth/status`
- `/auth/setup`
- `/auth/login`
- `/auth/me`
- `/auth/me/avatar`
- `/auth/logout`
- `get_current_user`

## Data Boundary

Owns local user authentication records through existing database access.

## Allowed Dependencies

May use `core.security`, `core.schemas`, avatar helpers, and database access.

## Forbidden Dependencies

Must not import chat, schedule, diary, persona review, or character repositories.

## Codex Notes

For auth tasks, read this README, `api.py`, and existing auth service code.
Avoid changing login behavior unless the user explicitly asks.

