"""Future diary API module.

The router is intentionally empty and is not included by backend/main.py yet.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/diary", tags=["diary"])

__all__ = ["router"]

