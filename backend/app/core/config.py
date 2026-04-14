"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings

# .env lives at project root (one level above backend/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Academe Tutors configuration. All values from .env or environment."""

    # Database
    database_url: str = "postgresql+asyncpg://localhost/academe_tutors"

    # AI (OpenRouter)
    openrouter_api_key: str = ""
    default_model: str = "anthropic/claude-sonnet-4-6"

    # Embedding
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072

    # Application
    backend_port: int = 8001
    frontend_url: str = "http://localhost:3782"
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3782"]

    # Optional
    brave_api_key: str = ""

    model_config = {
        "env_file": str(_PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
