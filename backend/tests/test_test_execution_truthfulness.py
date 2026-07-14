import asyncio
from pathlib import Path

from app.analysis.repository_analyzer import RepositoryAnalyzer, discover_test_paths
from app.events.manager import EventManager
from app.models.events import TerminalLogEvent
from app.pipeline.decision_engine import DecisionEngine
from app.pipeline.state import PipelineContext, PipelineStage
from app.verification.pytest_runner import (
    VerificationRunner,
    parse_node_test_output,
    parse_pytest_output,
    requires_pytest_addopts_fallback,
)


def test_discover_test_paths_supports_nested_and_file_targets(tmp_path: Path) -> None:
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    (tmp_path / "backend" / "tests" / "test_health.py").write_text("def test_health(): pass\n", encoding="utf-8")
    (tmp_path / "smoke_test.py").write_text("def test_smoke(): pass\n", encoding="utf-8")

    assert discover_test_paths(tmp_path) == ["backend/tests", "smoke_test.py"]
    assert RepositoryAnalyzer().analyze(tmp_path).test_paths == ["backend/tests", "smoke_test.py"]


def test_parse_empty_pytest_run_is_not_success() -> None:
    result = parse_pytest_output(5, "no tests ran in 0.01s", "python -m pytest -q")

    assert result.status == "no_tests"
    assert result.tests_total == 0
    assert result.tests_failed == 0
    assert result.error == "No runnable pytest tests were discovered."


def test_parse_passing_and_failing_runs_separately() -> None:
    passing = parse_pytest_output(0, "3 passed in 0.04s", "python -m pytest -q")
    failing = parse_pytest_output(1, "1 failed, 2 passed in 0.04s", "python -m pytest -q")

    assert passing.status == "passed"
    assert passing.tests_total == 3
    assert failing.status == "failed"
    assert failing.tests_total == 3
    assert failing.tests_failed == 1


def test_parse_failure_infers_source_from_conventional_test_module() -> None:
    output = (
        "FAILED tests/test_models.py::test_user_validation - "
        "AttributeError: User object has no attribute is_valid\n"
        "1 failed in 0.04s"
    )

    result = parse_pytest_output(1, output, "python -m pytest tests -q")

    assert result.failures[0]["source_file"] == "app/models.py"


def test_pytest_environment_failure_reports_missing_module_and_safe_retry_condition() -> None:
    coverage_error = parse_pytest_output(
        4,
        "ERROR: usage: python -m pytest [options]\npython -m pytest: error: unrecognized arguments: --cov=app\n",
        "python -m pytest tests -q",
    )
    missing_dependency = parse_pytest_output(
        2,
        "E   ModuleNotFoundError: No module named 'pydantic_settings'\n"
        "PytestConfigWarning: Unknown config option: asyncio_mode\n",
        "python -m pytest -o addopts= tests -q",
    )

    assert requires_pytest_addopts_fallback(coverage_error)
    assert not requires_pytest_addopts_fallback(missing_dependency)
    assert missing_dependency.status == "error"
    assert missing_dependency.missing_dependencies == ["pydantic_settings", "pytest-asyncio"]
    assert missing_dependency.error == "Test environment is missing Python module(s): pydantic_settings, pytest-asyncio."
    assert VerificationRunner.build_command(["tests"], ignore_addopts=True)[3:5] == ["-o", "addopts="]


def test_nested_pytest_project_uses_its_own_working_directory(tmp_path: Path) -> None:
    project = tmp_path / "backend"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_health.py").write_text("def test_health(): pass\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n",
        encoding="utf-8",
    )

    analysis = RepositoryAnalyzer().analyze(tmp_path)
    command = VerificationRunner.preview_command(
        tmp_path,
        analysis.test_paths,
        analysis.verification_command,
        analysis.test_framework,
        analysis.verification_workdir,
    )

    assert analysis.test_framework == "pytest"
    assert analysis.verification_workdir == "backend"
    assert analysis.test_paths == ["backend/tests"]
    assert command.endswith("-m pytest tests -q")


def test_next_project_without_a_test_script_does_not_fall_back_to_pytest(tmp_path: Path) -> None:
    app = tmp_path / "ecospher-temp"
    (app / "src" / "app").mkdir(parents=True)
    (app / "package.json").write_text(
        '{"dependencies":{"next":"16.0.0"},"scripts":{"build":"next build"}}',
        encoding="utf-8",
    )
    (app / "src" / "app" / "page.tsx").write_text("export default function Page() { return null; }\n", encoding="utf-8")

    analysis = RepositoryAnalyzer().analyze(tmp_path)

    assert analysis.language == "TypeScript"
    assert analysis.framework == "Next.js"
    assert analysis.test_framework == ""
    assert analysis.verification_command == []


def test_parse_node_test_summary_and_no_command_results_are_truthful() -> None:
    passed = parse_node_test_output(0, "Tests  3 passed (3)\n", "npm run test")
    no_command = VerificationRunner.no_runnable_tests_result()

    assert passed.status == "passed"
    assert passed.tests_total == 3
    assert passed.tests_passed == 3
    assert no_command.status == "no_tests"
    assert no_command.tests_total == 0
    assert no_command.error == "No runnable automated test suite was discovered."


def test_closed_event_session_replays_once_then_ends() -> None:
    async def consume_closed_session() -> list[str]:
        manager = EventManager()
        manager.create_session("completed-session")
        await manager.publish("completed-session", TerminalLogEvent(content="pipeline output"))
        await manager.close_session("completed-session")
        return [message async for message in manager.subscribe("completed-session")]

    messages = asyncio.run(consume_closed_session())

    assert len(messages) == 1
    assert "pipeline output" in messages[0]


def test_final_decision_never_claims_success_when_review_is_required() -> None:
    decision = DecisionEngine.generate_decision(
        PipelineContext(session_id="review-session", success=False),
        PipelineStage.STREAM_RESULTS,
    )

    assert "requires review" in decision.evidence
    assert "successfully" not in decision.evidence
    assert decision.confidence == 0.9
