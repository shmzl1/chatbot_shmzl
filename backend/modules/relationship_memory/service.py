"""Service for relationship memory events."""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from modules.relationship_memory.repository import relationship_memory_repository
from modules.relationship_memory.schemas import (
    RelationshipMemoryContext,
    RelationshipMemoryCreateRequest,
    RelationshipMemoryEvent,
)


class RelationshipMemoryService:
    def create(self, request: RelationshipMemoryCreateRequest) -> RelationshipMemoryEvent:
        return relationship_memory_repository.create(request)

    def list_active(
        self,
        *,
        character_id: str,
        limit: int = 100,
    ) -> List[RelationshipMemoryEvent]:
        return relationship_memory_repository.list_active(
            character_id=character_id,
            limit=limit,
        )

    def deactivate(self, event_id: int) -> RelationshipMemoryEvent:
        event = relationship_memory_repository.deactivate(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="relationship memory event not found")
        return event

    def debug(
        self,
        *,
        character_id: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        return relationship_memory_repository.debug(character_id=character_id, limit=limit)

    def get_context_for_character(
        self,
        *,
        character_id: str,
        limit: int = 20,
    ) -> RelationshipMemoryContext:
        return RelationshipMemoryContext(
            character_id=character_id,
            events=self.list_active(character_id=character_id, limit=limit),
        )

    def prompt_hits(self, *, character_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        events = relationship_memory_repository.list_prompt_events(
            character_id=character_id,
            limit=limit,
        )
        return [
            {
                "id": f"relmem_{event.id}",
                "source": "relationship_memory",
                "score": event.importance,
                "text": event.content,
                "payload": {
                    "id": event.id,
                    "memory_type": event.memory_type,
                    "content": event.content,
                    "importance": event.importance,
                    "source_type": event.source_type,
                    "source_id": event.source_id,
                    "source_turn_id": event.source_turn_id,
                    "evidence": event.evidence,
                    "is_pinned": event.is_pinned,
                    "read_policy": event.read_policy,
                    "status": event.status,
                    "expires_at": event.expires_at,
                },
            }
            for event in events
        ]

    def mark_prompt_hits_used(self, hits: List[Dict[str, Any]]) -> None:
        event_ids = [
            hit["payload"]["id"]
            for hit in hits
            if isinstance(hit.get("payload"), dict) and "id" in hit["payload"]
        ]
        relationship_memory_repository.mark_used(event_ids)


relationship_memory_service = RelationshipMemoryService()


def collect_from_chat(*args: Any, **kwargs: Any) -> RelationshipMemoryEvent:
    """Create a relationship memory event from chat-related input."""

    if args and isinstance(args[0], RelationshipMemoryCreateRequest):
        request = args[0]
    else:
        request = RelationshipMemoryCreateRequest(**kwargs)
    return relationship_memory_service.create(request)


def get_context_for_character(*args: Any, **kwargs: Any) -> RelationshipMemoryContext:
    return relationship_memory_service.get_context_for_character(*args, **kwargs)
