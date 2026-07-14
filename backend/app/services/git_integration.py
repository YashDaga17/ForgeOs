"""Git commit, push, and PR hooks with safe configuration gates."""

from __future__ import annotations

import asyncio
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

import httpx
from git import Repo

from app.config import Settings, get_settings


@dataclass
class GitIntegrationResult:
    committed: bool = False
    pushed: bool = False
    pull_request_created: bool = False
    pull_request_url: str = ""
    comparison_url: str = ""
    message: str = ""
    commit_sha: str = ""


class GitIntegrationService:
    """Commits locally and optionally pushes/opens PR when credentials exist."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def finalize(self, workspace_path: str | Path, repo_name: str) -> GitIntegrationResult:
        root = Path(workspace_path)
        if not (root / ".git").exists():
            return GitIntegrationResult(message="No git repository available for commit.")

        return await asyncio.to_thread(self._finalize_sync, root, repo_name)

    def _finalize_sync(self, root: Path, repo_name: str) -> GitIntegrationResult:
        repo = Repo(root)
        repo.config_writer().set_value("user", "name", self.settings.git_author_name).release()
        repo.config_writer().set_value("user", "email", self.settings.git_author_email).release()
        if not repo.is_dirty(untracked_files=True):
            return GitIntegrationResult(message="No code changes to commit.")

        base_branch = self._active_branch_name(repo)
        branch_name = f"forgeos/repair-{repo_name}".replace(" ", "-")
        if base_branch != branch_name:
            repo.git.checkout("-B", branch_name)
        repo.git.add(A=True)
        commit = repo.index.commit("ForgeOS automated repair")
        result = GitIntegrationResult(
            committed=True,
            commit_sha=commit.hexsha[:8],
            message=f"Committed repair changes on {branch_name}.",
        )

        if os.getenv("FORGEOS_ENABLE_GIT_PUSH", "false").lower() != "true":
            result.message += " Push/PR skipped; FORGEOS_ENABLE_GIT_PUSH is not true."
            return result

        try:
            origin = repo.remote("origin")
            self._push_branch(repo, origin, branch_name)
            result.pushed = True
            result.message += " Pushed branch to origin."
        except Exception as exc:
            result.message += f" Push failed: {exc}"
            return result

        result.comparison_url = self._build_comparison_url(repo, branch_name)
        repository = self._github_repository(origin.url)
        if repository is None:
            result.message += " PR creation is available for GitHub remotes only."
            return result
        if not self.settings.github_token:
            result.message += " GITHUB_TOKEN is not configured; open the compare URL to create a PR."
            return result

        try:
            result.pull_request_url = self._create_pull_request(
                owner=repository[0],
                repository=repository[1],
                head=branch_name,
                base=base_branch if base_branch != branch_name else "main",
            )
            result.pull_request_created = True
            result.message += " Created pull request."
        except (httpx.HTTPError, ValueError) as exc:
            result.message += f" Pull request creation failed: {exc}. Open the compare URL to create it manually."
        return result

    @staticmethod
    def _active_branch_name(repo: Repo) -> str:
        try:
            return repo.active_branch.name
        except TypeError:
            return "main"

    def _push_branch(self, repo: Repo, origin: Any, branch_name: str) -> None:
        remote_url = str(getattr(origin, "url", ""))
        if remote_url.startswith(("https://", "http://")) and self.settings.github_token:
            with self._git_askpass_environment(self.settings.github_token) as environment:
                with repo.git.custom_environment(**environment):
                    origin.push(refspec=f"{branch_name}:{branch_name}", set_upstream=True)
            return
        origin.push(refspec=f"{branch_name}:{branch_name}", set_upstream=True)

    @contextmanager
    def _git_askpass_environment(self, token: str) -> Iterator[dict[str, str]]:
        descriptor, script_path = tempfile.mkstemp(prefix="forgeos-git-askpass-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as script:
                script.write(
                    "#!/bin/sh\n"
                    "case \"$1\" in\n"
                    "  *Username*) printf '%s\\n' 'x-access-token' ;;\n"
                    "  *) printf '%s\\n' \"$FORGEOS_GIT_PUSH_TOKEN\" ;;\n"
                    "esac\n"
                )
            os.chmod(script_path, 0o700)
            yield {
                "GIT_ASKPASS": script_path,
                "GIT_TERMINAL_PROMPT": "0",
                "FORGEOS_GIT_PUSH_TOKEN": token,
            }
        finally:
            Path(script_path).unlink(missing_ok=True)

    def _create_pull_request(self, owner: str, repository: str, head: str, base: str) -> str:
        if not self.settings.github_token:
            raise ValueError("GITHUB_TOKEN is required to create a pull request")

        endpoint = f"{self.settings.github_api_base.rstrip('/')}/repos/{owner}/{repository}/pulls"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.settings.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "title": "ForgeOS automated repair",
            "head": head,
            "base": base,
            "body": "Automated repair created by ForgeOS after the verification pipeline passed.",
        }
        with httpx.Client(timeout=15.0) as client:
            response = client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        pull_request_url = str(response.json().get("html_url", ""))
        if not pull_request_url:
            raise ValueError("GitHub created a pull request without an html_url")
        return pull_request_url

    @staticmethod
    def _github_repository(remote_url: str) -> tuple[str, str] | None:
        if remote_url.startswith("git@github.com:"):
            repository_path = remote_url.removeprefix("git@github.com:")
        else:
            parsed = urlparse(remote_url)
            if parsed.hostname != "github.com":
                return None
            repository_path = parsed.path.lstrip("/")

        parts = repository_path.removesuffix(".git").split("/")
        if len(parts) != 2 or not all(parts):
            return None
        return parts[0], parts[1]

    @staticmethod
    def _build_comparison_url(repo: Repo, branch_name: str) -> str:
        try:
            repository = GitIntegrationService._github_repository(repo.remote("origin").url)
        except Exception:
            return ""
        if repository is None:
            return ""
        return f"https://github.com/{repository[0]}/{repository[1]}/compare/{branch_name}?expand=1"
