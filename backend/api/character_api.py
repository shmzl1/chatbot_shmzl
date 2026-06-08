"""Compatibility wrapper for character routes.

Character APIs now live in `modules.characters.api`.
"""

from modules.characters.api import router

__all__ = ["router"]
