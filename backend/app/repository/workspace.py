"""
Workspace preparation for ForgeOS runs.

Supports GitHub cloning for real repositories and a deterministic local demo
copy for reliable judge demos.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from git import Repo

from app.config import Settings, get_settings


@dataclass(frozen=True)
class WorkspaceResult:
    repo_name: str
    workspace_path: Path
    source: str
    display_url: str


class WorkspaceService:
    """Creates isolated per-session workspaces."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def prepare(self, repository_url: str, session_id: str) -> WorkspaceResult:
        """Prepare a workspace by cloning GitHub or copying the local demo repo."""
        self.settings.workspace_root.mkdir(parents=True, exist_ok=True)
        repo_name = repository_name(repository_url)
        target = self.settings.workspace_root / session_id / repo_name
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)

        if is_demo_repository(repository_url):
            await asyncio.to_thread(
                shutil.copytree,
                self.settings.demo_repository_path,
                target,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git"),
            )
            await self._ensure_git_repo(target)
            return WorkspaceResult(
                repo_name=repo_name,
                workspace_path=target,
                source="demo",
                display_url=str(self.settings.demo_repository_path),
            )

        if not is_allowed_git_url(repository_url):
            raise ValueError("Only GitHub repository URLs or the bundled demo repository are supported.")

        await asyncio.to_thread(Repo.clone_from, repository_url, target)
        return WorkspaceResult(
            repo_name=repo_name,
            workspace_path=target,
            source="github",
            display_url=repository_url,
        )

    async def _ensure_git_repo(self, workspace_path: Path) -> None:
        def init_repo() -> None:
            repo = Repo.init(workspace_path)
            repo.git.add(A=True)
            if not repo.head.is_valid():
                repo.index.commit("Initial demo repository state")

        await asyncio.to_thread(init_repo)


def is_demo_repository(repository_url: str) -> bool:
    normalized = repository_url.strip().lower()
    return normalized in {
        "",
        "demo",
        "local",
        "local://demo",
        "demo://forgeos",
        "https://github.com/example/fastapi-demo",
    }


def repository_name(repository_url: str) -> str:
    if is_demo_repository(repository_url):
        return "forgeos-demo-repository"
    parsed = urlparse(repository_url)
    name = parsed.path.rstrip("/").split("/")[-1].removesuffix(".git")
    return name or "repository"


def is_allowed_git_url(repository_url: str) -> bool:
    parsed = urlparse(repository_url)
    return parsed.scheme in {"https", "http"} and parsed.netloc.lower() in {
        "github.com",
        "www.github.com",
    }

