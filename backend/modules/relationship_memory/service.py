"""Future shared relationship memory service boundary.

This module is intentionally not wired into existing business flows yet.
Functions raise NotImplementedError so callers do not mistake the placeholder
for a working persistence layer.
"""

from typing import Any

from modules.relationship_memory.schemas import RelationshipMemoryContext


def collect_from_chat(*args: Any, **kwargs: Any) -> None:
    """Collect relationship memory from ordinary chat in a future iteration."""

    raise NotImplementedError("relationship_memory collection from chat is not implemented yet.")


def collect_from_schedule(*args: Any, **kwargs: Any) -> None:
    """Collect relationship memory from schedule planning or review later."""

    raise NotImplementedError("relationship_memory collection from schedule is not implemented yet.")


def collect_from_diary(*args: Any, **kwargs: Any) -> None:
    """Collect relationship memory from diary reading sessions later."""

    raise NotImplementedError("relationship_memory collection from diary is not implemented yet.")


def get_context_for_character(*args: Any, **kwargs: Any) -> RelationshipMemoryContext:
    """Read shared relationship context for a character in a future iteration."""

    raise NotImplementedError("relationship_memory context lookup is not implemented yet.")

