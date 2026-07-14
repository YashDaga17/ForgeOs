"""
Business intelligence collection.

GitHub metadata is the primary source. When a repository is local, private, or
GitHub is unavailable, ForgeOS falls back to repository-derived signals so the
demo still produces honest insight instead of static placeholder data.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.services.ai_insights import AIInsightsService


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str


@dataclass
class BusinessIntelligence:
    stars: int = 0
    forks: int = 0
    contributors: int = 0
    open_issues: int = 0
    watchers: int = 0
    release_cadence: str = "Local demo repository"
    dependency_health: str = "No dependency manifest found"
    community_activity: str = "Local-only signal"
    executive_summary: str = ""
    source: str = "local"
    repository_owner: str = ""
    repository_name: str = ""
    primary_language: str = ""
    license: str = ""
    topics: list[str] = field(default_factory=list)
    competitor_snapshot: list[dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""
    ai_status: str = "not_requested"
    ai_model: str = ""
    ai_message: str = ""
    ai_product_thesis: str = ""
    ai_engineering_risk: str = ""
    ai_next_move: str = ""
    ai_confidence: float = 0.0
    ai_request_id: str = ""
    ai_input_tokens: int = 0
    ai_output_tokens: int = 0

    def as_event_payload(self) -> dict[str, Any]:
        return {
            "stars": self.stars,
            "forks": self.forks,
            "contributors": self.contributors,
            "open_issues": self.open_issues,
            "watchers": self.watchers,
            "release_cadence": self.release_cadence,
            "dependency_health": self.dependency_health,
            "community_activity": self.community_activity,
            "executive_summary": self.executive_summary,
            "source": self.source,
            "repository_owner": self.repository_owner,
            "repository_name": self.repository_name,
            "primary_language": self.primary_language,
            "license": self.license,
            "topics": self.topics,
            "competitor_snapshot": self.competitor_snapshot,
            "last_updated": self.last_updated,
            "ai_status": self.ai_status,
            "ai_model": self.ai_model,
            "ai_message": self.ai_message,
            "ai_product_thesis": self.ai_product_thesis,
            "ai_engineering_risk": self.ai_engineering_risk,
            "ai_next_move": self.ai_next_move,
            "ai_confidence": self.ai_confidence,
            "ai_request_id": self.ai_request_id,
            "ai_input_tokens": self.ai_input_tokens,
            "ai_output_tokens": self.ai_output_tokens,
        }


class BusinessIntelligenceService:
    """Collects GitHub-first business data with local fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.ai_insights = AIInsightsService(self.settings)

    async def collect(
        self,
        *,
        repository_url: str,
        workspace_path: str,
        repository_name: str,
        total_files: int,
        total_lines: int,
        tests_total: int,
        tests_failed: int,
        issues_fixed: int,
        primary_language: str = "",
    ) -> BusinessIntelligence:
        github_repo = parse_github_repository(repository_url)
        if github_repo:
            github_data = await self._collect_github(github_repo)
            if github_data:
                github_data.dependency_health = dependency_health(Path(workspace_path))
                intelligence = github_data
            else:
                intelligence = self._collect_local(
                    repository_name=repository_name,
                    workspace_path=workspace_path,
                    total_files=total_files,
                    total_lines=total_lines,
                    tests_total=tests_total,
                    tests_failed=tests_failed,
                    issues_fixed=issues_fixed,
                    primary_language=primary_language,
                )
        else:
            intelligence = self._collect_local(
                repository_name=repository_name,
                workspace_path=workspace_path,
                total_files=total_files,
                total_lines=total_lines,
                tests_total=tests_total,
                tests_failed=tests_failed,
                issues_fixed=issues_fixed,
                primary_language=primary_language,
            )

        intelligence.dependency_health = dependency_health(Path(workspace_path))
        intelligence.executive_summary = build_executive_summary(
            intelligence,
            total_files=total_files,
            total_lines=total_lines,
            tests_total=tests_total,
            tests_failed=tests_failed,
            issues_fixed=issues_fixed,
        )
        return await self._enrich_with_ai(
            intelligence,
            total_files=total_files,
            total_lines=total_lines,
            tests_total=tests_total,
            tests_failed=tests_failed,
            issues_fixed=issues_fixed,
        )

    async def _collect_github(self, repo: GitHubRepository) -> BusinessIntelligence | None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.github_api_base,
                headers=headers,
                timeout=8.0,
            ) as client:
                repo_response, contributors_response, releases_response = await asyncio.gather(
                    client.get(f"/repos/{repo.owner}/{repo.name}"),
                    client.get(f"/repos/{repo.owner}/{repo.name}/contributors", params={"per_page": 100}),
                    client.get(f"/repos/{repo.owner}/{repo.name}/releases", params={"per_page": 10}),
                )
                repo_response.raise_for_status()
                repo_payload = repo_response.json()

                contributors = 0
                if contributors_response.status_code < 400:
                    contributors = len(contributors_response.json())

                releases: list[dict[str, Any]] = []
                if releases_response.status_code < 400:
                    releases = releases_response.json()

                competitors = await self._collect_competitors(client, repo_payload)

            bi = BusinessIntelligence(
                stars=int(repo_payload.get("stargazers_count") or 0),
                forks=int(repo_payload.get("forks_count") or 0),
                contributors=contributors,
                open_issues=int(repo_payload.get("open_issues_count") or 0),
                watchers=int(repo_payload.get("subscribers_count") or repo_payload.get("watchers_count") or 0),
                release_cadence=release_cadence(releases, repo_payload.get("pushed_at")),
                community_activity=community_activity(repo_payload),
                source="github",
                repository_owner=repo.owner,
                repository_name=repo.name,
                primary_language=repo_payload.get("language") or "",
                license=(repo_payload.get("license") or {}).get("spdx_id") or "",
                topics=repo_payload.get("topics") or [],
                competitor_snapshot=competitors,
                last_updated=repo_payload.get("updated_at") or "",
            )
            return bi
        except Exception:
            return None

    async def _collect_competitors(
        self,
        client: httpx.AsyncClient,
        repo_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        topics = repo_payload.get("topics") or []
        language = repo_payload.get("language")
        query_parts = []
        if topics:
            query_parts.append(f"topic:{topics[0]}")
        if language:
            query_parts.append(f"language:{language}")
        if not query_parts:
            return []

        try:
            response = await client.get(
                "/search/repositories",
                params={
                    "q": " ".join(query_parts),
                    "sort": "stars",
                    "per_page": 5,
                },
            )
            response.raise_for_status()
            current_full_name = repo_payload.get("full_name")
            competitors = []
            for item in response.json().get("items", []):
                if item.get("full_name") == current_full_name:
                    continue
                competitors.append(
                    {
                        "name": item.get("full_name", ""),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "description": item.get("description") or "",
                    }
                )
                if len(competitors) == 3:
                    break
            return competitors
        except Exception:
            return []

    def _collect_local(
        self,
        *,
        repository_name: str,
        workspace_path: str,
        total_files: int,
        total_lines: int,
        tests_total: int,
        tests_failed: int,
        issues_fixed: int,
        primary_language: str,
    ) -> BusinessIntelligence:
        workspace = Path(workspace_path)
        return BusinessIntelligence(
            source="local",
            repository_name=repository_name,
            primary_language=primary_language or "Unknown",
            release_cadence="Local demo repository; no remote releases",
            dependency_health=dependency_health(workspace),
            community_activity=(
                f"{tests_total} tests observed, {issues_fixed} fixes prepared"
                if tests_total
                else "Repository analyzed locally"
            ),
            competitor_snapshot=[],
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    async def _enrich_with_ai(
        self,
        intelligence: BusinessIntelligence,
        *,
        total_files: int,
        total_lines: int,
        tests_total: int,
        tests_failed: int,
        issues_fixed: int,
    ) -> BusinessIntelligence:
        facts = {
            "repository": {
                "name": intelligence.repository_name,
                "source": intelligence.source,
                "language": intelligence.primary_language,
                "license": intelligence.license or "unknown",
                "topics": intelligence.topics,
            },
            "github_metrics": {
                "stars": intelligence.stars,
                "forks": intelligence.forks,
                "contributors": intelligence.contributors,
                "open_issues": intelligence.open_issues,
                "watchers": intelligence.watchers,
                "release_cadence": intelligence.release_cadence,
                "community_activity": intelligence.community_activity,
            },
            "engineering_signals": {
                "files": total_files,
                "lines": total_lines,
                "tests_total": tests_total,
                "tests_failed": tests_failed,
                "issues_fixed": issues_fixed,
                "dependency_health": intelligence.dependency_health,
            },
            "competitors": intelligence.competitor_snapshot,
        }
        result = await self.ai_insights.summarize_business_intelligence(facts)
        intelligence.ai_status = result.status
        intelligence.ai_model = result.model
        intelligence.ai_message = result.message
        intelligence.ai_request_id = result.request_id
        intelligence.ai_input_tokens = result.input_tokens
        intelligence.ai_output_tokens = result.output_tokens
        if result.brief:
            intelligence.executive_summary = result.brief.executive_summary
            intelligence.ai_product_thesis = result.brief.product_thesis
            intelligence.ai_engineering_risk = result.brief.engineering_risk
            intelligence.ai_next_move = result.brief.next_move
            intelligence.ai_confidence = result.brief.confidence
        return intelligence


def parse_github_repository(repository_url: str) -> GitHubRepository | None:
    parsed = urlparse(repository_url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    return GitHubRepository(owner=parts[0], name=parts[1].removesuffix(".git"))


def dependency_health(workspace: Path) -> str:
    candidates = [workspace / "requirements.txt", workspace / "pyproject.toml", workspace / "package.json"]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            lines = [
                line.strip()
                for line in candidate.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        except OSError:
            continue
        if candidate.name == "requirements.txt":
            return f"{len(lines)} Python dependencies tracked; vulnerability scan not configured"
        return f"{candidate.name} present; ecosystem metadata ready"
    return "No dependency manifest found"


def release_cadence(releases: list[dict[str, Any]], pushed_at: str | None) -> str:
    if len(releases) >= 2:
        return f"{len(releases)} recent GitHub releases detected"
    if len(releases) == 1:
        return "One GitHub release detected"
    if pushed_at:
        return f"No releases; last pushed {pushed_at[:10]}"
    return "No release data available"


def community_activity(repo_payload: dict[str, Any]) -> str:
    pushed_at = repo_payload.get("pushed_at")
    watchers = repo_payload.get("subscribers_count") or repo_payload.get("watchers_count") or 0
    if pushed_at:
        return f"Last push {pushed_at[:10]} with {watchers} watchers"
    return f"{watchers} watchers on GitHub"


def build_executive_summary(
    bi: BusinessIntelligence,
    *,
    total_files: int,
    total_lines: int,
    tests_total: int,
    tests_failed: int,
    issues_fixed: int,
) -> str:
    source = "GitHub" if bi.source == "github" else "local repository"
    quality = (
        f"{tests_total - tests_failed}/{tests_total} tests passing after repair planning"
        if tests_total
        else "test signal unavailable"
    )
    traction = (
        f"{bi.stars:,} stars, {bi.forks:,} forks, and {bi.contributors} contributors"
        if bi.source == "github"
        else f"{total_files} files and {total_lines:,} lines analyzed locally"
    )
    return (
        f"ForgeOS used {source} intelligence for {bi.repository_name or 'the repository'}. "
        f"Traction signal: {traction}. Engineering signal: {quality}; "
        f"{issues_fixed} issues fixed or prepared for verification. "
        f"Dependency signal: {bi.dependency_health}."
    )
