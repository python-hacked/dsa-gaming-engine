from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    app_base_url: str = "http://127.0.0.1:8000"
    session_secret: str = "dev-only-change-me"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/auth/google/callback"
    database_url: str = ""
    piston_api_url: str = "https://emkc.org/api/v2/piston"
    admin_signup_secret: str = ""
    gemini_api_key: str = ""

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())

    @property
    def database_configured(self) -> bool:
        url = self.database_url.strip()
        return url.startswith("postgresql") and "USER:PASSWORD@HOST" not in url


@lru_cache
def get_settings() -> Settings:
    return Settings()
