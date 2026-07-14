"""Async repository-owned test command execution with live line streaming."""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable


LineCallback = Callable[[str, bool], Awaitable[None]]


@dataclass
class PytestResult:
    return_code: int
    output: str
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    failures: list[dict[str, str]] = field(default_factory=list)
    status: str = "error"
    command: str = ""
    error: str = ""
    warning: str = ""
    missing_dependencies: list[str] = field(default_factory=list)


class VerificationRunner:
    """Runs the explicit verification command discovered in a workspace."""

    async def run(
        self,
        workspace_path: str | Path,
        on_line: LineCallback | None = None,
        test_paths: list[str] | None = None,
        command: list[str] | None = None,
        working_directory: str = "",
        framework: str = "pytest",
    ) -> PytestResult:
        root = Path(workspace_path).resolve()
        cwd = (root / working_directory).resolve()
        try:
            cwd.relative_to(root)
        except ValueError:
            return PytestResult(
                return_code=1,
                output="",
                status="error",
                command=shlex.join(command or []),
                error="Verification working directory is outside the repository workspace.",
            )
        if not cwd.is_dir():
            return PytestResult(
                return_code=1,
                output="",
                status="error",
                command=shlex.join(command or []),
                error=f"Verification working directory does not exist: {working_directory or '.'}",
            )

        resolved_test_paths = self._relative_test_paths(root, cwd, test_paths or [])
        resolved_command = list(command or [])
        if not resolved_command and framework == "pytest":
            resolved_command = self.build_command(resolved_test_paths)
        if not resolved_command:
            return self.no_runnable_tests_result()

        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join((str(cwd), str(root)))
        result = await self._execute_command(
            resolved_command,
            cwd,
            env,
            on_line,
            framework,
        )
        if framework == "pytest" and not command and requires_pytest_addopts_fallback(result):
            retry_command = self.build_command(resolved_test_paths, ignore_addopts=True)
            notice = (
                "[QA] pytest-cov is unavailable in the ForgeOS verification environment; "
                "retrying without the repository coverage addopts."
            )
            if on_line:
                await on_line(notice, False)
                await on_line(f"$ {shlex.join(retry_command)}", False)
            retry = await self._execute_command(retry_command, cwd, env, on_line, framework)
            retry.output = "\n".join(part for part in (result.output, notice, retry.output) if part)
            retry.warning = (
                "Repository coverage addopts were skipped because pytest-cov is unavailable; "
                "coverage enforcement was not evaluated."
            )
            return retry
        return result

    async def _execute_command(
        self,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
        on_line: LineCallback | None,
        framework: str,
    ) -> PytestResult:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            return PytestResult(
                return_code=127,
                output="",
                status="error",
                command=shlex.join(command),
                error=f"Verification command is unavailable: {command[0]}",
            )

        lines: list[str] = []
        assert process.stdout is not None
        async for raw in process.stdout:
            line = raw.decode(errors="replace").rstrip()
            lines.append(line)
            if on_line:
                await on_line(line, is_error_line(line))

        return_code = await process.wait()
        output = "\n".join(lines)
        display_command = shlex.join(command)
        if framework == "pytest":
            return parse_pytest_output(return_code, output, command=display_command)
        return parse_node_test_output(return_code, output, command=display_command)

    @staticmethod
    def build_command(test_paths: list[str], *, ignore_addopts: bool = False) -> list[str]:
        # An empty target lets pytest perform its own standard discovery.
        addopts_override = ["-o", "addopts="] if ignore_addopts else []
        return [sys.executable, "-m", "pytest", *addopts_override, *(test_paths or []), "-q"]

    @staticmethod
    def preview_command(
        workspace_path: str | Path,
        test_paths: list[str],
        command: list[str],
        framework: str,
        working_directory: str = "",
    ) -> str:
        root = Path(workspace_path).resolve()
        cwd = (root / working_directory).resolve()
        resolved_test_paths = VerificationRunner._relative_test_paths(root, cwd, test_paths)
        resolved_command = command or (VerificationRunner.build_command(resolved_test_paths) if framework == "pytest" else [])
        return shlex.join(resolved_command) if resolved_command else ""

    @staticmethod
    def _relative_test_paths(root: Path, cwd: Path, test_paths: list[str]) -> list[str]:
        resolved_paths: list[str] = []
        for test_path in test_paths:
            candidate = (root / test_path).resolve()
            try:
                resolved_paths.append(candidate.relative_to(cwd).as_posix())
            except ValueError:
                resolved_paths.append(test_path)
        return resolved_paths

    @staticmethod
    def no_runnable_tests_result() -> PytestResult:
        return PytestResult(
            return_code=0,
            output="",
            status="no_tests",
            error="No runnable automated test suite was discovered.",
        )


# Compatibility alias for callers imported before verification became multi-runtime.
PytestRunner = VerificationRunner


def is_error_line(line: str) -> bool:
    lowered = line.lower()
    return line.startswith("FAILED ") or line.startswith("E ") or " failed" in lowered or "error" in lowered


def parse_pytest_output(return_code: int, output: str, command: str = "") -> PytestResult:
    result = PytestResult(return_code=return_code, output=output, command=command)
    summary_line = next(
        (
            line
            for line in reversed(output.splitlines())
            if any(token in line for token in (" passed", " failed", " skipped", " error", "errors", "no tests ran"))
        ),
        "",
    )
    for count, label in re.findall(r"(\d+) (failed|passed|skipped|error|errors)", summary_line):
        value = int(count)
        if label == "passed":
            result.tests_passed = value
        elif label == "failed":
            result.tests_failed = value
        elif label == "skipped":
            result.tests_skipped = value
        elif label in {"error", "errors"}:
            result.tests_failed += value

    result.tests_total = result.tests_passed + result.tests_failed + result.tests_skipped
    result.failures = parse_failures(output)
    if result.tests_failed == 0 and return_code != 0 and result.failures:
        result.tests_failed = len(result.failures)
        result.tests_total = result.tests_passed + result.tests_failed + result.tests_skipped
    lowered_output = output.lower()
    missing_dependencies = missing_python_dependencies(output)
    if missing_dependencies:
        result.status = "error"
        result.missing_dependencies = missing_dependencies
        result.error = f"Test environment is missing Python module(s): {', '.join(missing_dependencies)}."
    elif "no tests ran" in lowered_output or "file or directory not found" in lowered_output:
        result.status = "no_tests"
        result.error = "No runnable pytest tests were discovered."
    elif result.tests_failed > 0:
        result.status = "failed"
    elif return_code == 0 and result.tests_total > 0:
        result.status = "passed"
    elif return_code != 0:
        result.status = "error"
        result.error = last_error_line(output) or f"pytest exited with code {return_code}."
    else:
        result.status = "no_tests"
        result.error = "No runnable pytest tests were discovered."
    return result


def requires_pytest_addopts_fallback(result: PytestResult) -> bool:
    """Only bypass coverage addopts when their plugin is unavailable."""
    output = result.output.lower()
    return result.status == "error" and "unrecognized arguments" in output and "--cov" in output


def missing_python_dependencies(output: str) -> list[str]:
    matches = re.findall(r"No module named ['\"]([^'\"]+)['\"]", output)
    lowered_output = output.lower()
    if "unknown config option: asyncio_mode" in lowered_output or "pytest.mark.asyncio" in output:
        matches.append("pytest-asyncio")
    return sorted(set(matches))


def parse_node_test_output(return_code: int, output: str, command: str = "") -> PytestResult:
    """Parse common Jest/Vitest/Playwright summaries without faking test counts."""
    result = PytestResult(return_code=return_code, output=output, command=command)
    lowered_output = output.lower()
    if any(marker in lowered_output for marker in ("no test files found", "no tests found", "no tests to run")):
        result.status = "no_tests"
        result.error = "The repository test command ran but did not discover any tests."
        return result

    summaries = re.findall(
        r"(?:^|\n)\s*tests?\s*:?[\t ]+(?:(\d+)\s+failed[\s,]*)?(?:(\d+)\s+passed[\s,]*)?(?:(\d+)\s+skipped)?",
        output,
        flags=re.IGNORECASE,
    )
    if summaries:
        failed, passed, skipped = summaries[-1]
        result.tests_failed = int(failed or 0)
        result.tests_passed = int(passed or 0)
        result.tests_skipped = int(skipped or 0)
    else:
        jest_summary = re.search(r"Tests:\s*(\d+)\s+failed,?\s*(\d+)\s+passed", output, re.IGNORECASE)
        if jest_summary:
            result.tests_failed = int(jest_summary.group(1))
            result.tests_passed = int(jest_summary.group(2))

    result.tests_total = result.tests_passed + result.tests_failed + result.tests_skipped
    if result.tests_failed > 0:
        result.status = "failed"
    elif return_code == 0 and result.tests_total > 0:
        result.status = "passed"
    elif return_code != 0:
        result.status = "error"
        result.error = last_error_line(output) or f"Test command exited with code {return_code}."
    else:
        result.status = "no_tests"
        result.error = "The test command did not report a runnable test result."
    return result


def last_error_line(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped and (stripped.startswith("ERROR") or stripped.startswith("E ")):
            return stripped
    return ""


def parse_failures(output: str) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in output.splitlines():
        if line.startswith("FAILED "):
            parts = line.split(" - ", 1)
            location = parts[0].removeprefix("FAILED ").strip()
            error = parts[1].strip() if len(parts) > 1 else ""
            file_name, _, test_name = location.partition("::")
            current = {
                "test": test_name or location,
                "file": file_name,
                "error": error,
                "type": classify_error(error),
                "source_file": infer_source_file(test_name or location, error, file_name),
            }
            failures.append(current)
        elif current and line.startswith("E ") and not current["error"]:
            current["error"] = line.removeprefix("E ").strip()
            current["type"] = classify_error(current["error"])
            current["source_file"] = infer_source_file(current["test"], current["error"], current["file"])
    return failures


def classify_error(error: str) -> str:
    lowered = error.lower()
    if "attributeerror" in lowered:
        return "attribute_error"
    if "assert" in lowered or "assertionerror" in lowered:
        return "assertion_error"
    if "importerror" in lowered or "modulenotfounderror" in lowered:
        return "import_error"
    return "test_failure"


def infer_source_file(test_name: str, error: str, test_file: str = "") -> str:
    lowered = f"{test_name} {error}".lower()
    if "user" in lowered and "is_valid" in lowered:
        return "app/models.py"
    if "item" in lowered and ("404" in lowered or "not_found" in lowered):
        return "app/main.py"
    test_path = Path(test_file)
    if test_path.name.startswith("test_") and test_path.suffix == ".py":
        module_name = test_path.stem.removeprefix("test_")
        if module_name:
            return f"app/{module_name}.py"
    return ""
