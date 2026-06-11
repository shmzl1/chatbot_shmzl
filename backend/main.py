from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from modules.auth.api import router as auth_router
from modules.chat.api import router as chat_router
from modules.characters.api import router as character_router
from modules.debug.api import router as debug_router
from modules.diary.api import router as diary_router
from modules.health.api import router as health_router
from modules.knowledge.api import router as knowledge_router
from modules.memory.api import router as memory_router
from modules.persona_review.api import router as feedback_router
from modules.relationship_memory.api import router as relationship_memory_router
from modules.voice.api import router as voice_router
from services.auth_service import auth_service
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
app.include_router(diary_router)
app.include_router(feedback_router)
app.include_router(knowledge_router)
app.include_router(memory_router)
app.include_router(relationship_memory_router)
app.include_router(voice_router)


@app.on_event("startup")
def run_database_migrations() -> None:
    database_service.ensure_ready()
    auth_service.ensure_default_user()


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
