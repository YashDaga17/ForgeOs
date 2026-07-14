"""Deterministic source dependency and change-impact analysis."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}
MAX_GRAPH_NODES = 48
ScriptAlias = tuple[str, str, Path]


@dataclass(frozen=True)
class GraphAnalysis:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, str]]
    truncated: bool


def build_source_graph(
    root: Path,
    source_paths: list[Path],
    file_records: dict[str, dict[str, Any]],
    entry_points: list[str],
) -> GraphAnalysis:
    """Build a file-level graph from Python AST and JS/TS local imports."""
    root = root.resolve()
    candidates = [path for path in source_paths if path.suffix in SOURCE_SUFFIXES]
    module_index = _build_python_module_index(root, candidates)
    script_aliases = _load_script_aliases(root)
    all_edges: set[tuple[str, str]] = set()

    for path in candidates:
        source = path.relative_to(root).as_posix()
        if path.suffix == ".py":
            targets = _python_import_targets(path, root, module_index)
        else:
            targets = _script_import_targets(path, root, script_aliases)
        all_edges.update((source, target) for target in targets if target != source)

    all_node_ids = {path.relative_to(root).as_posix() for path in candidates}
    edge_node_ids = {node for edge in all_edges for node in edge}
    priority = sorted(
        all_node_ids,
        key=lambda node: (
            node not in entry_points,
            node not in edge_node_ids,
            -int(file_records.get(node, {}).get("lines", 0)),
            node,
        ),
    )
    included = set(priority[:MAX_GRAPH_NODES])
    edges = [
        {"from": source, "to": target, "kind": "imports"}
        for source, target in sorted(all_edges)
        if source in included and target in included
    ]
    included_nodes = priority[:MAX_GRAPH_NODES]
    labels = _display_labels(included_nodes)
    nodes = [
        {
            "id": node,
            "label": labels[node],
            "path": node,
            "kind": str(file_records.get(node, {}).get("type", "source")),
            "lines": int(file_records.get(node, {}).get("lines", 0)),
            "entry_point": node in entry_points,
        }
        for node in included_nodes
    ]
    return GraphAnalysis(nodes=nodes, edges=edges, truncated=len(all_node_ids) > len(nodes))


def calculate_blast_radius(
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, str]],
    focus_files: list[str],
) -> dict[str, Any]:
    """Report the real import reach of a proposed source change."""
    known_nodes = {str(node.get("id")) for node in graph_nodes}
    focus = [path for path in dict.fromkeys(focus_files) if path in known_nodes]
    if not focus:
        return {
            "focus_files": [],
            "affected_files": [],
            "inbound_dependents": 0,
            "outbound_dependencies": 0,
            "risk": "low",
            "message": "No graph-resolved source file is associated with this action.",
        }

    reverse: dict[str, set[str]] = {node: set() for node in known_nodes}
    forward: dict[str, set[str]] = {node: set() for node in known_nodes}
    for edge in graph_edges:
        source = str(edge.get("from", ""))
        target = str(edge.get("to", ""))
        if source in forward and target in reverse:
            forward[source].add(target)
            reverse[target].add(source)

    inbound = _walk_graph(reverse, focus)
    outbound = _walk_graph(forward, focus)
    affected = sorted((inbound | outbound) - set(focus))
    risk = "high" if len(inbound) >= 6 or len(affected) >= 10 else "medium" if affected else "low"
    return {
        "focus_files": focus,
        "affected_files": affected,
        "inbound_dependents": len(inbound - set(focus)),
        "outbound_dependencies": len(outbound - set(focus)),
        "risk": risk,
        "message": (
            f"{len(affected)} graph-connected file(s) are in the change radius "
            f"for {', '.join(focus)}."
        ),
    }


def _walk_graph(adjacency: dict[str, set[str]], start: list[str]) -> set[str]:
    visited = set(start)
    frontier = list(start)
    while frontier:
        current = frontier.pop()
        for neighbor in adjacency.get(current, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)
    return visited


def _build_python_module_index(root: Path, source_paths: list[Path]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in source_paths:
        if path.suffix != ".py":
            continue
        relative = path.relative_to(root)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            index[".".join(parts)] = relative.as_posix()
    return index


def _python_import_targets(path: Path, root: Path, module_index: dict[str, str]) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return set()

    relative = path.relative_to(root)
    package_parts = list(relative.parent.parts)
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved = _resolve_python_module(alias.name, module_index)
                if resolved:
                    targets.add(resolved)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                prefix = package_parts[: max(0, len(package_parts) - node.level + 1)]
            else:
                prefix = []
            module_parts = node.module.split(".") if node.module else []
            base = ".".join([*prefix, *module_parts])
            resolved = _resolve_python_module(base, module_index)
            if resolved:
                targets.add(resolved)
            for alias in node.names:
                resolved_alias = _resolve_python_module(".".join(part for part in (base, alias.name) if part), module_index)
                if resolved_alias:
                    targets.add(resolved_alias)
    return targets


def _resolve_python_module(module_name: str, module_index: dict[str, str]) -> str | None:
    if not module_name:
        return None
    if module_name in module_index:
        return module_index[module_name]
    parts = module_name.split(".")
    while len(parts) > 1:
        parts.pop()
        candidate = ".".join(parts)
        if candidate in module_index:
            return module_index[candidate]
    return None


_SCRIPT_IMPORT = re.compile(
    r"(?:import|export)\s+(?:[^\"']+?\s+from\s+)?[\"']([^\"']+)[\"']|require\(\s*[\"']([^\"']+)[\"']\s*\)"
)


def _script_import_targets(path: Path, root: Path, aliases: list[ScriptAlias]) -> set[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    targets: set[str] = set()
    for first, second in _SCRIPT_IMPORT.findall(content):
        specifier = first or second
        resolved = _resolve_script_path(path, specifier, root, aliases)
        if resolved:
            targets.add(resolved)
    return targets


def _resolve_script_path(
    path: Path,
    specifier: str,
    root: Path,
    aliases: list[ScriptAlias],
) -> str | None:
    if specifier.startswith("."):
        base = (path.parent / specifier).resolve()
    else:
        base = _resolve_alias_base(specifier, aliases)
        if base is None:
            return None
    candidates = [base]
    candidates.extend(base.with_suffix(suffix) for suffix in SOURCE_SUFFIXES)
    candidates.extend(base / f"index{suffix}" for suffix in SOURCE_SUFFIXES)
    for candidate in candidates:
        if candidate.is_file():
            try:
                return candidate.relative_to(root).as_posix()
            except ValueError:
                return None
    return None


def _load_script_aliases(root: Path) -> list[ScriptAlias]:
    """Read TypeScript/JavaScript path aliases from repository config files."""
    aliases: list[ScriptAlias] = []
    for config_path in sorted([*root.rglob("tsconfig.json"), *root.rglob("jsconfig.json")]):
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        compiler_options = data.get("compilerOptions", {})
        paths = compiler_options.get("paths", {}) if isinstance(compiler_options, dict) else {}
        if not isinstance(paths, dict):
            continue
        base_url = compiler_options.get("baseUrl", ".") if isinstance(compiler_options, dict) else "."
        config_root = (config_path.parent / str(base_url)).resolve()
        for pattern, targets in paths.items():
            if not isinstance(pattern, str) or not isinstance(targets, list):
                continue
            for target in targets:
                if isinstance(target, str):
                    aliases.append((pattern, target, config_root))
    return sorted(aliases, key=lambda alias: len(alias[0]), reverse=True)


def _resolve_alias_base(specifier: str, aliases: list[ScriptAlias]) -> Path | None:
    for pattern, target, config_root in aliases:
        if "*" in pattern:
            prefix, suffix = pattern.split("*", 1)
            if not specifier.startswith(prefix) or (suffix and not specifier.endswith(suffix)):
                continue
            wildcard = specifier[len(prefix) : len(specifier) - len(suffix) if suffix else None]
            resolved_target = target.replace("*", wildcard)
        elif specifier == pattern:
            resolved_target = target
        else:
            continue
        return (config_root / resolved_target).resolve()
    return None


def _display_labels(nodes: list[str]) -> dict[str, str]:
    """Use concise names, widening duplicate labels until each is unambiguous."""
    parts = {node: Path(node).parts for node in nodes}
    depths = {node: 1 for node in nodes}
    while True:
        labels = {
            node: "/".join(parts[node][-depths[node] :])
            for node in nodes
        }
        duplicates: dict[str, list[str]] = {}
        for node, label in labels.items():
            duplicates.setdefault(label, []).append(node)
        collisions = [group for group in duplicates.values() if len(group) > 1]
        if not collisions:
            return labels
        expanded = False
        for group in collisions:
            for node in group:
                if depths[node] < len(parts[node]):
                    depths[node] += 1
                    expanded = True
        if not expanded:
            return {node: node for node in nodes}
