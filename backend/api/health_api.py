from fastapi import APIRouter

from core.schemas import HealthResponse
from services.database_service import database_service


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    postgres_ready = database_service.is_ready()
    return HealthResponse(
        status="ok" if postgres_ready else "degraded",
        gptsovits=False,
        qdrant=False,
        postgres=postgres_ready,
    )
