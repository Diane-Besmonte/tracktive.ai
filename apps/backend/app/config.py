from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os  # NEW

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "Tracktive AI"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    TAVILY_API_KEY: str | None = None
    SERPAPI_API_KEY: str | None = None

    APP_ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"
    TZ: str = "Asia/Manila"

    SECRET_KEY: str = "dev-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

settings = Settings()

# --- IMPORTANT: export to process env so SDKs see it ---
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.LANGSMITH_API_KEY:
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
if settings.LANGSMITH_PROJECT:
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
if settings.LANGSMITH_ENDPOINT:
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
