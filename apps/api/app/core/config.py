import json
from typing import Annotated, Any

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(v: Any) -> list[str]:
    """
    Parses CORS origins from environment variables.
    Handles JSON list formats (e.g. '["http://localhost:3000"]')
    or simple comma-separated lists (e.g. 'http://localhost:3000,http://localhost:3001').
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return [x.strip() for x in v.split(",") if x.strip()]
    return v

class Settings(BaseSettings):
    """
    Application Settings configuration.
    Uses pydantic-settings to automatically bind environment variables.
    All secrets must be provided via the environment; no hardcoded defaults are used.
    """

    # Project Information
    PROJECT_NAME: str = "ThreatWeave API"
    ENVIRONMENT: str = "development"

    # API Configuration
    PORT: int = 8000

    # Allowed CORS Origins for API access
    CORS_ALLOWED_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors_origins)] = Field(

        ["http://localhost:3000"], validation_alias="CORS_ALLOWED_ORIGINS"
    )


    # PostgreSQL Database URL connection string.
    # Read from DATABASE_URL environment variable.
    # Must be supplied in environment or .env file (no default).
    DATABASE_URL: str = Field(..., validation_alias="DATABASE_URL")

    # Chroma Vector DB storage directory or endpoint path.
    # Read from CHROMA_PATH environment variable.
    # Must be supplied in environment or .env file (no default).
    CHROMA_PATH: str = Field(..., validation_alias="CHROMA_PATH")

    # ChromaDB & RAG configurations (Phase 12)
    CHROMA_HOST: str = Field("localhost", validation_alias="CHROMA_HOST")
    CHROMA_PORT: int = Field(8001, validation_alias="CHROMA_PORT")
    RAG_SIMILARITY_THRESHOLD: float = Field(0.40, validation_alias="RAG_SIMILARITY_THRESHOLD")
    RAG_TOP_K: int = Field(5, validation_alias="RAG_TOP_K")

    # API Key for Groq LLM inference API.
    # Read from GROQ_API_KEY environment variable.
    # Must be supplied in environment or .env file (no default).
    GROQ_API_KEY: str = Field(..., validation_alias="GROQ_API_KEY")

    # API Key for OpenAI GPT models (Optional for other multimodal capabilities).
    # Read from OPENAI_API_KEY environment variable.
    # Defaults to None if not supplied, but no default secret key.
    OPENAI_API_KEY: str | None = Field(None, validation_alias="OPENAI_API_KEY")

    # API Key for Tavily search engine (Optional for web lookup agent capabilities).
    # Read from TAVILY_API_KEY environment variable.
    # Defaults to None if not supplied, but no default secret key.
    TAVILY_API_KEY: str | None = Field(None, validation_alias="TAVILY_API_KEY")

    # Storage and Validation configurations
    STORAGE_PATH: str = Field("./storage", validation_alias="STORAGE_PATH")
    MAX_IMAGE_SIZE_MB: int = Field(10, validation_alias="MAX_IMAGE_SIZE_MB")
    MAX_AUDIO_SIZE_MB: int = Field(15, validation_alias="MAX_AUDIO_SIZE_MB")
    MAX_TEXT_CHARS: int = Field(20000, validation_alias="MAX_TEXT_CHARS")

    # Text Agent configurations.
    # Model: openai/gpt-oss-120b — largest available on this Groq account,
    # supports JSON mode, strong instruction-following for structured
    # threat analysis output. Verified live via models.list() on 2026-09-06.
    TEXT_AGENT_MODEL: str = Field("openai/gpt-oss-120b", validation_alias="TEXT_AGENT_MODEL")
    TEXT_AGENT_TIMEOUT: int = Field(30, validation_alias="TEXT_AGENT_TIMEOUT")

    # URL Agent configurations (Phase 6).
    # URL_REPUTATION_API_KEY is OPTIONAL — leave empty to disable reputation checks.
    # When unset, the URL Agent runs heuristics-only with no network calls.
    URL_REPUTATION_API_KEY: str = Field("", validation_alias="URL_REPUTATION_API_KEY")
    URL_REPUTATION_API_TIMEOUT_SECONDS: int = Field(
        8, validation_alias="URL_REPUTATION_API_TIMEOUT_SECONDS"
    )

    # n8n Workflow Automation configurations (Phase 16)
    N8N_PORT: int = Field(5678, validation_alias="N8N_PORT")
    N8N_WEBHOOK_URL: str = Field("", validation_alias="N8N_WEBHOOK_URL")
    N8N_ALERT_SEVERITY_THRESHOLD: str = Field("high", validation_alias="N8N_ALERT_SEVERITY_THRESHOLD")

    # Auth & JWT configurations (Phase 17)
    JWT_SECRET_KEY: str = Field("threatweave-dev-secret-key-change-in-prod", validation_alias="JWT_SECRET_KEY")
    JWT_EXPIRY_MINUTES: int = Field(60 * 24, validation_alias="JWT_EXPIRY_MINUTES")
    JWT_ALGORITHM: str = Field("HS256", validation_alias="JWT_ALGORITHM")

    # Configuration for setting env file lookup behavior.
    # We look for a .env file first, but it can be overridden by system environments.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra env variables not specified in the model
    )

settings = Settings()
