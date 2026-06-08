# Persona Review Module

Compatibility wrapper for persona feedback routes currently implemented in
`backend/api/feedback_api.py`.

Character-scoped persona review routes under
`/characters/{character_id}/persona-review/...` are exposed from
`modules.characters.api` and call the existing persona review service.
