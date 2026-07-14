"""Deterministic repository analysis and verification discovery."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.analysis.dependency_graph import build_source_graph


IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}


@dataclass
class RepositoryAnalysis:
    total_files: int
    total_lines: int
    files: list[dict[str, Any]]
    language: str
    framework: str
    test_framework: str
    test_paths: list[str]
    verification_command: list[str]
    verification_workdir: str
    modules: list[dict[str, Any]]
    dependencies: list[dict[str, str]]
    graph_nodes: list[dict[str, Any]]
    graph_edges: list[dict[str, str]]
    graph_truncated: bool
    entry_points: list[str]
    architecture_summary: str


class RepositoryAnalyzer:
    """Scans files, framework signals, modules, and local dependencies."""

    def analyze(self, workspace_path: str | Path) -> RepositoryAnalysis:
        root = Path(workspace_path).resolve()
        files: list[dict[str, Any]] = []
        total_lines = 0
        module_counts: Counter[str] = Counter()
        entry_points: list[str] = []
        source_paths: list[Path] = []
        file_records: dict[str, dict[str, Any]] = {}

        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
                continue
            rel = path.relative_to(root).as_posix()
            file_type = classify_file(rel)
            line_count = count_lines(path)
            total_lines += line_count
            record = {"path": rel, "lines": line_count, "type": file_type}
            files.append(record)
            file_records[rel] = record

            module = rel.split("/", 1)[0]
            module_counts[module] += 1
            if rel.endswith(".py") and looks_like_fastapi_entry(path):
                entry_points.append(rel)
            if looks_like_next_entry(path, rel):
                entry_points.append(rel)
            if path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                source_paths.append(path)

        test_paths = discover_test_paths(root)
        test_framework, verification_command, verification_workdir = detect_verification_configuration(
            root,
            test_paths,
            detect_language(files),
        )
        if test_framework == "pytest":
            test_paths = python_test_paths(root, test_paths)
        language = "Python" if test_framework == "pytest" else detect_language(files)
        preferred_root = root / verification_workdir if test_framework == "pytest" else None
        framework = detect_framework(root, preferred_root=preferred_root)
        graph = build_source_graph(root, source_paths, file_records, entry_points)
        modules = [
            {"name": name, "type": module_type(name), "files": count}
            for name, count in module_counts.most_common()
        ]
        dependency_rows = aggregate_module_dependencies(graph.edges)

        return RepositoryAnalysis(
            total_files=len(files),
            total_lines=total_lines,
            files=files,
            language=language,
            framework=framework,
            test_framework=test_framework,
            test_paths=test_paths,
            verification_command=verification_command,
            verification_workdir=verification_workdir,
            modules=modules,
            dependencies=dependency_rows,
            graph_nodes=graph.nodes,
            graph_edges=graph.edges,
            graph_truncated=graph.truncated,
            entry_points=entry_points,
            architecture_summary=architecture_summary(
                language=language,
                framework=framework,
                test_framework=test_framework,
                module_count=len(modules),
                dependency_count=len(graph.edges),
            ),
        )


def classify_file(path: str) -> str:
    path_parts = path.split("/")
    if (
        path.startswith(("tests/", "test/"))
        or any(part in {"tests", "test", "__tests__"} or part.startswith("test_") for part in path_parts)
        or path.endswith(("_test.py", ".test.ts", ".test.tsx", ".test.js", ".test.jsx", ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx"))
    ):
        return "test"
    if path.startswith(".github/"):
        return "ci"
    if path.endswith((".md", ".rst")):
        return "docs"
    if path.endswith((".toml", ".txt", ".yaml", ".yml", ".json", ".ini")):
        return "config"
    return "source"


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return 0


def detect_language(files: list[dict[str, Any]]) -> str:
    """Identify the dominant source language without treating docs as code."""
    counts: Counter[str] = Counter()
    for file in files:
        path = str(file["path"])
        if path.endswith(".py"):
            counts["Python"] += 1
        elif path.endswith((".ts", ".tsx")):
            counts["TypeScript"] += 1
        elif path.endswith((".js", ".jsx")):
            counts["JavaScript"] += 1
    return counts.most_common(1)[0][0] if counts else "Unknown"


def detect_framework(root: Path, preferred_root: Path | None = None) -> str:
    """Prefer the application that owns the selected verification target."""
    if preferred_root is not None:
        return detect_fastapi_framework(preferred_root)

    for package_path, package in package_manifests(root):
        dependencies: set[str] = set()
        for section in (package.get("dependencies", {}), package.get("devDependencies", {})):
            if isinstance(section, dict):
                dependencies.update(str(name) for name in section)
        if "next" in dependencies or any(package_path.parent.glob("next.config.*")):
            return "Next.js"
        if "@nestjs/core" in dependencies:
            return "NestJS"
        if "vite" in dependencies:
            return "Vite"

    return detect_fastapi_framework(root)


def detect_fastapi_framework(root: Path) -> str:
    manifests = []
    for manifest in ("requirements.txt", "pyproject.toml"):
        candidate = root / manifest
        if candidate.exists():
            manifests.append(candidate.read_text(encoding="utf-8", errors="ignore").lower())
    if "fastapi" in "\n".join(manifests):
        return "FastAPI"
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if "fastapi" in path.read_text(encoding="utf-8", errors="ignore").lower():
            return "FastAPI"
    return ""


def discover_test_paths(root: Path) -> list[str]:
    """Return real Python and JavaScript test locations without inventing targets."""
    directories: set[str] = set()
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        parts = relative.split("/")
        if any(part in {"tests", "test", "__tests__"} for part in parts[:-1]):
            directory = "/".join(parts[: next(i for i, part in enumerate(parts) if part in {"tests", "test", "__tests__"}) + 1])
            directories.add(directory)
        elif is_test_file(path):
            files.append(relative)
    return sorted(directories | set(files))


def detect_verification_configuration(
    root: Path,
    test_paths: list[str],
    language: str,
) -> tuple[str, list[str], str]:
    """Select one explicit, repository-owned test command when it exists.

    ForgeOS does not infer an ``npx`` command or install dependencies. A cloned
    repository must declare its own test script before its JavaScript tests are
    considered runnable.
    """
    npm_command, npm_workdir = discover_npm_test_command(root)
    has_python_tests = has_python_test_targets(root, test_paths)
    if has_python_tests or has_pytest_configuration(root):
        return "pytest", [], discover_pytest_workdir(root, test_paths)
    if language in {"TypeScript", "JavaScript"} and npm_command:
        return "npm", npm_command, npm_workdir
    if npm_command:
        return "npm", npm_command, npm_workdir
    return "", [], ""


def has_python_test_targets(root: Path, test_paths: list[str]) -> bool:
    for relative in test_paths:
        path = root / relative
        if path.is_file() and path.suffix == ".py":
            return True
        if path.is_dir() and any(candidate.suffix == ".py" for candidate in path.rglob("*.py")):
            return True
    return False


def python_test_paths(root: Path, test_paths: list[str]) -> list[str]:
    """Keep frontend test files out of a pytest command in a mixed repository."""
    python_paths: list[str] = []
    for relative in test_paths:
        path = root / relative
        if path.is_file() and path.suffix == ".py":
            python_paths.append(relative)
        elif path.is_dir() and any(candidate.suffix == ".py" for candidate in path.rglob("*.py")):
            python_paths.append(relative)
    return python_paths


def discover_pytest_workdir(root: Path, test_paths: list[str]) -> str:
    """Use the closest pytest configuration above a discovered Python test."""
    checked: set[Path] = set()
    for relative in test_paths:
        candidate = root / relative
        start = candidate if candidate.is_dir() else candidate.parent
        for directory in (start, *start.parents):
            if directory in checked:
                continue
            checked.add(directory)
            try:
                directory.relative_to(root)
            except ValueError:
                break
            if has_pytest_configuration_at(directory):
                relative_directory = directory.relative_to(root).as_posix()
                return "" if relative_directory == "." else relative_directory
    return ""


def package_manifests(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    manifests: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.rglob("package.json")):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        try:
            package = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(package, dict):
            manifests.append((path, package))
    return manifests


def discover_npm_test_command(root: Path) -> tuple[list[str], str]:
    """Find an explicit npm test script, preferring the conventional name."""
    script_names = ("test", "test:unit", "test:ci", "test:e2e")
    for package_path, package in package_manifests(root):
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            continue
        script_name = next((name for name in script_names if isinstance(scripts.get(name), str)), None)
        if script_name:
            relative = package_path.parent.relative_to(root).as_posix()
            return ["npm", "run", script_name], "" if relative == "." else relative
    return [], ""


def has_pytest_configuration(root: Path) -> bool:
    return has_pytest_configuration_at(root)


def has_pytest_configuration_at(root: Path) -> bool:
    for manifest in ("pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml"):
        path = root / manifest
        if not path.exists():
            continue
        if manifest == "pytest.ini":
            return True
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "pytest" in text:
            return True
    return False


def is_test_file(path: Path) -> bool:
    name = path.name
    return (
        path.suffix == ".py" and (name.startswith("test_") or name.endswith("_test.py"))
    ) or name.endswith((".test.ts", ".test.tsx", ".test.js", ".test.jsx", ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx"))


def aggregate_module_dependencies(graph_edges: list[dict[str, str]]) -> list[dict[str, str]]:
    """Collapse file-level imports into the existing top-level module summary."""
    dependencies = {
        (edge["from"].split("/", 1)[0], edge["to"].split("/", 1)[0])
        for edge in graph_edges
        if edge.get("from") and edge.get("to")
    }
    return [
        {"from": source, "to": target}
        for source, target in sorted(dependencies)
        if source != target
    ]


def looks_like_fastapi_entry(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "FastAPI(" in text and "app =" in text


def looks_like_next_entry(path: Path, relative: str) -> bool:
    return path.name == "page.tsx" and "/app/" in f"/{relative}"


def module_type(name: str) -> str:
    lowered = name.lower()
    if lowered == "tests":
        return "testing"
    if lowered in {"app", "src"}:
        return "application"
    if "api" in lowered or "route" in lowered:
        return "routes"
    if "model" in lowered:
        return "data"
    if "service" in lowered:
        return "business_logic"
    return "module"


def architecture_summary(
    *,
    language: str,
    framework: str,
    test_framework: str,
    module_count: int,
    dependency_count: int,
) -> str:
    stack = " / ".join(part for part in (language, framework, test_framework) if part)
    return (
        f"{stack or 'Repository'} project with {module_count} top-level modules "
        f"and {dependency_count} detected local dependency links. "
        "ForgeOS is using deterministic file and import analysis for this pass."
    )
