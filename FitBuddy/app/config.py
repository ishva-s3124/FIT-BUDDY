from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    app_env: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./data/fitbuddy.db"
    gemini_api_key: str = ""
    workout_model: str = "gemini-3.8-flash"
    fast_model: str = "gemini-3.8-flash"
    demo_mode: bool = False
    ai_fallback_to_demo: bool = True
    admin_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
