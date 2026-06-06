import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


def _data_dir() -> Path:
    configured = os.getenv("DATA_DIR")
    if not configured:
        return BASE_DIR / "data"

    path = Path(configured)
    if path.is_absolute():
        return path

    return BASE_DIR / path


def _path_from_env(name: str, default: Path) -> Path:
    configured = os.getenv(name)
    if not configured:
        return default

    path = Path(configured)
    if path.is_absolute():
        return path

    return BASE_DIR / path


def _database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot",
    )


def _gptsovits_base_url() -> str:
    return os.getenv("GPTSOVITS_BASE_URL", "http://127.0.0.1:9880").rstrip("/")


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    value = value.strip()
    return value or None


def _openai_base_url() -> str | None:
    value = _optional_env("OPENAI_BASE_URL")
    if not value:
        return None

    value = value.rstrip("/")
    for suffix in ("/chat/completions", "/v1/chat/completions"):
        if value.endswith(suffix):
            return value[: -len(suffix)]

    return value


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Local Role Voice Chatbot")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    data_dir: Path = _data_dir()
    database_url: str = _database_url()
    outputs_dir: Path = _path_from_env("OUTPUTS_DIR", BASE_DIR / "outputs")
    upload_dir: Path = _path_from_env("UPLOAD_DIR", BASE_DIR / "data" / "uploads")
    frontend_dir: Path = _path_from_env("FRONTEND_DIR", PROJECT_ROOT / "frontend" / "simple_web")
    default_character_id: str = os.getenv("DEFAULT_CHARACTER_ID", "role01")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str | None = _optional_env("OPENAI_API_KEY")
    openai_base_url: str | None = _openai_base_url()
    openai_model: str | None = _optional_env("OPENAI_MODEL")
    openai_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))
    debug_prompt: bool = os.getenv("DEBUG_PROMPT", "false").lower() == "true"
    top_k_lore: int = int(os.getenv("TOP_K_LORE", "5"))
    top_k_dialogue: int = int(os.getenv("TOP_K_DIALOGUE", "5"))
    top_k_reaction: int = int(os.getenv("TOP_K_REACTION", "3"))
    top_k_memory: int = int(os.getenv("TOP_K_MEMORY", "5"))
    style_score_threshold: float = float(os.getenv("STYLE_SCORE_THRESHOLD", "8.0"))
    gptsovits_base_url: str = _gptsovits_base_url()
    gptsovits_timeout_seconds: float = float(os.getenv("GPTSOVITS_TIMEOUT_SECONDS", "120"))
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change_me_dev_jwt_secret")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))
    avatar_max_size_mb: int = int(os.getenv("AVATAR_MAX_SIZE_MB", "5"))


settings = Settings()
