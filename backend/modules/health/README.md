# Health Module

## Module Responsibility

Lightweight health checks for local development.

## Not Responsible For

Business diagnostics, database export, character validation, or admin actions.

## Public Interfaces

- `GET /health`

## Data Boundary

Read-only status checks.

## Allowed Dependencies

May use settings and database readiness helpers.

## Forbidden Dependencies

Must not mutate data or start/stop external services.

## Codex Notes

Keep health checks fast and side-effect free.
