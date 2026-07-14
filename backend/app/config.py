"""
ForgeOS runtime configuration.

Centralizes environment-backed settings without leaking secrets into logs or
events. Defaults are chosen for a reliable local demo, with GitHub/OpenAI
features enabled automatically when credentials are present.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")


class Settings(BaseModel):
    """Environment-backed application settings."""

    project_root: Path = PROJECT_ROOT
    backend_root: Path = BACKEND_ROOT
    demo_repository_path: Path = BACKEND_ROOT / "demo_repository"
    workspace_root: Path = BACKEND_ROOT / "app" / "workspaces"

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_repair_model: str = os.getenv("OPENAI_REPAIR_MODEL", "gpt-5.6")
    openai_bi_model: str = os.getenv("OPENAI_BI_MODEL", "gpt-5.6-luna")
    openai_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "15"))
    allow_demo_ai_fallback: bool = Field(
        default_factory=lambda: os.getenv("FORGEOS_ALLOW_DEMO_AI_FALLBACK", "false").lower() == "true"
    )

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_api_base: str = os.getenv("GITHUB_API_BASE", "https://api.github.com")

    git_author_name: str = os.getenv("FORGEOS_GIT_AUTHOR_NAME", "ForgeOS")
    git_author_email: str = os.getenv("FORGEOS_GIT_AUTHOR_EMAIL", "forgeos@example.com")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
