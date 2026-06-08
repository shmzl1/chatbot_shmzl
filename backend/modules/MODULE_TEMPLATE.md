# Module Name

## Module Responsibility

Describe what this module owns. Keep this section short and concrete.

## Not Responsible For

List responsibilities that belong to other modules.

## Public Interfaces

List FastAPI routes and public service methods that other modules may call.

## Internal File Responsibilities

- `api.py`: HTTP request/response boundary only.
- `service.py`: business logic and orchestration.
- `repository.py`: database or filesystem persistence boundary.
- `schemas.py`: module request/response models.
- `README.md`: module ownership, dependency rules, and debugging notes.

## Allowed Dependencies

List modules or shared utilities this module may import.

## Forbidden Dependencies

List modules or repositories this module must not import.

## Data Boundary

Document owned tables, files, directories, and external services.

## Error Handling

Explain how database, filesystem, LLM, or external-service errors should be exposed.
Do not hide errors with mock fallbacks.

## Debugging

Explain how to verify this module locally without running long tasks.

## Codex Notes

Before editing this module, read this README and the directly related files.
Avoid cross-module changes unless the public interface requires them.
