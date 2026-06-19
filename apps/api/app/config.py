"""Application configuration.

Settings are loaded from environment variables (see .env.example). Paths to the
shared JSON registries in packages/shared/data are resolved relative to this
file's location so the backend always reads the exact same files the frontend
bundles, never a second hand-copied version.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/app/config.py -> parents[0]=app, [1]=api, [2]=apps, [3]=repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHARED_DATA_DIR = _REPO_ROOT / "packages" / "shared" / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "firip-api"
    app_version: str = "0.1.0"
    environment: str = "development"
    git_sha: str | None = None
    build_time: str | None = None

    database_url: str = "sqlite+aiosqlite:///:memory:"

    cors_origins: str = "http://localhost:3000"

    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    auth_dev_bypass: bool = False

    run_live_smoke_tests: bool = False

    nws_user_agent: str = "firip.app (ops@firip.app)"

    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    notifications_provider: str | None = None
    notifications_api_key: str | None = None

    # Shared registry JSON file paths (read-only inputs from packages/shared).
    counties_json_path: Path = _SHARED_DATA_DIR / "counties.json"
    sources_json_path: Path = _SHARED_DATA_DIR / "sources.json"
    scoring_json_path: Path = _SHARED_DATA_DIR / "scoring.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
