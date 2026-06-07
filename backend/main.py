from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.auth_api import router as auth_router
from api.chat_api import router as chat_router
from api.character_api import router as character_router
from api.debug_api import router as debug_router
from api.feedback_api import router as feedback_router
from api.health_api import router as health_router
from api.knowledge_api import router as knowledge_router
from api.memory_api import router as memory_router
from api.voice_api import router as voice_router
from core.config import settings
from services.database_service import database_service


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(character_router)
app.include_router(chat_router)
app.include_router(debug_router)
app.include_router(feedback_router)
app.include_router(knowledge_router)
app.include_router(memory_router)
app.include_router(voice_router)


@app.on_event("startup")
def run_database_migrations() -> None:
    database_service.ensure_ready()


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse(url="/app/")


if settings.frontend_dir.exists():
    app.mount(
        "/app",
        StaticFiles(directory=settings.frontend_dir, html=True),
        name="app",
    )

settings.outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/outputs",
    StaticFiles(directory=settings.outputs_dir),
    name="outputs",
)

settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir),
    name="uploads",
)
