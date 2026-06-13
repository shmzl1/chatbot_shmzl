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


def _llm_base_url(name: str) -> str | None:
    value = _optional_env(name)
    if not value:
        return None

    value = value.rstrip("/")
    for suffix in ("/chat/completions", "/v1/chat/completions"):
        if value.endswith(suffix):
            return value[: -len(suffix)]

    return value


def _optional_float_env(name: str) -> float | None:
    value = _optional_env(name)
    if value is None:
        return None
    return float(value)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Virtual Character Companion System")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    data_dir: Path = _data_dir()
    database_url: str = _database_url()
    outputs_dir: Path = _path_from_env("OUTPUTS_DIR", BASE_DIR / "outputs")
    upload_dir: Path = _path_from_env("UPLOAD_DIR", BASE_DIR / "data" / "uploads")
    default_character_id: str = os.getenv("DEFAULT_CHARACTER_ID", "role01")
    chat_llm_provider: str | None = _optional_env("CHAT_LLM_PROVIDER")
    chat_openai_api_key: str | None = _optional_env("CHAT_OPENAI_API_KEY")
    chat_openai_base_url: str | None = _llm_base_url("CHAT_OPENAI_BASE_URL")
    chat_openai_model: str | None = _optional_env("CHAT_OPENAI_MODEL")
    chat_openai_timeout_seconds: float | None = _optional_float_env("CHAT_OPENAI_TIMEOUT_SECONDS")
    chat_openai_temperature: float | None = _optional_float_env("CHAT_OPENAI_TEMPERATURE")
    persona_editor_llm_provider: str | None = _optional_env("PERSONA_EDITOR_LLM_PROVIDER")
    persona_editor_openai_api_key: str | None = _optional_env("PERSONA_EDITOR_OPENAI_API_KEY")
    persona_editor_openai_base_url: str | None = _llm_base_url("PERSONA_EDITOR_OPENAI_BASE_URL")
    persona_editor_openai_model: str | None = _optional_env("PERSONA_EDITOR_OPENAI_MODEL")
    persona_editor_openai_timeout_seconds: float | None = _optional_float_env("PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS")
    persona_editor_openai_temperature: float | None = _optional_float_env("PERSONA_EDITOR_OPENAI_TEMPERATURE")
    debug_prompt: bool = os.getenv("DEBUG_PROMPT", "false").lower() == "true"
    top_k_lore: int = int(os.getenv("TOP_K_LORE", "5"))
    top_k_dialogue: int = int(os.getenv("TOP_K_DIALOGUE", "5"))
    top_k_reaction: int = int(os.getenv("TOP_K_REACTION", "3"))
    top_k_memory: int = int(os.getenv("TOP_K_MEMORY", "5"))
    style_score_threshold: float = float(os.getenv("STYLE_SCORE_THRESHOLD", "8.0"))
    gptsovits_base_url: str = _gptsovits_base_url()
    gptsovits_timeout_seconds: float = float(os.getenv("GPTSOVITS_TIMEOUT_SECONDS", "120"))
    avatar_max_size_mb: int = int(os.getenv("AVATAR_MAX_SIZE_MB", "5"))
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    )
    cors_methods: tuple[str, ...] = ("OPTIONS", "GET", "POST", "PUT", "PATCH", "DELETE")
    cors_headers: tuple[str, ...] = ("*",)

    def get_llm_config(self, profile: str) -> dict:
        if profile == "chat":
            return {
                "profile": profile,
                "provider": self.chat_llm_provider,
                "api_key": self.chat_openai_api_key,
                "base_url": self.chat_openai_base_url,
                "model": self.chat_openai_model,
                "timeout_seconds": self.chat_openai_timeout_seconds,
                "temperature": self.chat_openai_temperature,
                "missing_labels": {
                    "provider": "CHAT_LLM_PROVIDER",
                    "api_key": "CHAT_OPENAI_API_KEY",
                    "base_url": "CHAT_OPENAI_BASE_URL",
                    "model": "CHAT_OPENAI_MODEL",
                    "timeout_seconds": "CHAT_OPENAI_TIMEOUT_SECONDS",
                    "temperature": "CHAT_OPENAI_TEMPERATURE",
                },
            }

        if profile == "persona_editor":
            return {
                "profile": profile,
                "provider": self.persona_editor_llm_provider,
                "api_key": self.persona_editor_openai_api_key,
                "base_url": self.persona_editor_openai_base_url,
                "model": self.persona_editor_openai_model,
                "timeout_seconds": self.persona_editor_openai_timeout_seconds,
                "temperature": self.persona_editor_openai_temperature,
                "missing_labels": {
                    "provider": "PERSONA_EDITOR_LLM_PROVIDER",
                    "api_key": "PERSONA_EDITOR_OPENAI_API_KEY",
                    "base_url": "PERSONA_EDITOR_OPENAI_BASE_URL",
                    "model": "PERSONA_EDITOR_OPENAI_MODEL",
                    "timeout_seconds": "PERSONA_EDITOR_OPENAI_TIMEOUT_SECONDS",
                    "temperature": "PERSONA_EDITOR_OPENAI_TEMPERATURE",
                },
            }

        raise ValueError(f"Unsupported LLM profile '{profile}'.")


settings = Settings()
