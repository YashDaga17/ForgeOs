from pathlib import Path
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.services.git_integration import GitIntegrationService


def test_extracts_github_repository_from_supported_remote_urls() -> None:
    service = GitIntegrationService(Settings())

    assert service._github_repository("git@github.com:owner/repository.git") == ("owner", "repository")
    assert service._github_repository("https://github.com/owner/repository.git") == ("owner", "repository")
    assert service._github_repository("https://gitlab.com/owner/repository.git") is None


def test_creates_pull_request_through_github_api() -> None:
    service = GitIntegrationService(
        Settings(github_token="test-token", github_api_base="https://api.github.test")
    )
    response = MagicMock()
    response.json.return_value = {"html_url": "https://github.com/owner/repository/pull/42"}

    with patch("app.services.git_integration.httpx.Client") as client_class:
        client = client_class.return_value.__enter__.return_value
        client.post.return_value = response

        pull_request_url = service._create_pull_request(
            owner="owner",
            repository="repository",
            head="forgeos/repair-repository",
            base="main",
        )

    assert pull_request_url == "https://github.com/owner/repository/pull/42"
    response.raise_for_status.assert_called_once()
    client.post.assert_called_once_with(
        "https://api.github.test/repos/owner/repository/pulls",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer test-token",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "title": "ForgeOS automated repair",
            "head": "forgeos/repair-repository",
            "base": "main",
            "body": "Automated repair created by ForgeOS after the verification pipeline passed.",
        },
    )


def test_git_askpass_script_keeps_the_token_out_of_the_file() -> None:
    service = GitIntegrationService(Settings(github_token="test-token"))

    with service._git_askpass_environment("test-token") as environment:
        script_path = Path(environment["GIT_ASKPASS"])
        script = script_path.read_text()
        assert "test-token" not in script
        assert environment["FORGEOS_GIT_PUSH_TOKEN"] == "test-token"

    assert not script_path.exists()
