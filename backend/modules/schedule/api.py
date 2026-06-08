"""Future schedule API module.

The router is intentionally empty and is not included by backend/main.py yet.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/schedule", tags=["schedule"])

__all__ = ["router"]

