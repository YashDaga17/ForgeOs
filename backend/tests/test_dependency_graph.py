from pathlib import Path

from app.analysis.dependency_graph import calculate_blast_radius
from app.analysis.repository_analyzer import RepositoryAnalyzer


def test_repository_analysis_builds_real_file_import_graph(tmp_path: Path) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "main.py").write_text(
        "from app.service import load_record\n\ndef run():\n    return load_record()\n",
        encoding="utf-8",
    )
    (app / "service.py").write_text(
        "from app.models import record\n\ndef load_record():\n    return record\n",
        encoding="utf-8",
    )
    (app / "models.py").write_text("record = {'id': 1}\n", encoding="utf-8")

    analysis = RepositoryAnalyzer().analyze(tmp_path)
    edge_pairs = {(edge["from"], edge["to"]) for edge in analysis.graph_edges}

    assert {node["id"] for node in analysis.graph_nodes} == {
        "app/main.py",
        "app/service.py",
        "app/models.py",
    }
    assert ("app/main.py", "app/service.py") in edge_pairs
    assert ("app/service.py", "app/models.py") in edge_pairs


def test_blast_radius_uses_real_import_reach() -> None:
    impact = calculate_blast_radius(
        [
            {"id": "app/main.py"},
            {"id": "app/service.py"},
            {"id": "app/models.py"},
        ],
        [
            {"from": "app/main.py", "to": "app/service.py", "kind": "imports"},
            {"from": "app/service.py", "to": "app/models.py", "kind": "imports"},
        ],
        ["app/models.py"],
    )

    assert impact["focus_files"] == ["app/models.py"]
    assert impact["affected_files"] == ["app/main.py", "app/service.py"]
    assert impact["inbound_dependents"] == 2
    assert impact["outbound_dependencies"] == 0
    assert impact["risk"] == "medium"


def test_repository_analysis_resolves_typescript_aliases_and_unique_page_labels(tmp_path: Path) -> None:
    app_root = tmp_path / "web"
    (app_root / "src" / "app" / "reports").mkdir(parents=True)
    (app_root / "src" / "app" / "social").mkdir(parents=True)
    (app_root / "src" / "components").mkdir()
    (app_root / "package.json").write_text(
        '{"dependencies":{"next":"16.0.0"},"scripts":{"test":"vitest run"}}',
        encoding="utf-8",
    )
    (app_root / "tsconfig.json").write_text(
        '{"compilerOptions":{"paths":{"@/*":["./src/*"]}}}',
        encoding="utf-8",
    )
    (app_root / "src" / "components" / "Header.tsx").write_text(
        "export function Header() { return null; }\n",
        encoding="utf-8",
    )
    (app_root / "src" / "app" / "reports" / "page.tsx").write_text(
        'import { Header } from "@/components/Header";\nexport default Header;\n',
        encoding="utf-8",
    )
    (app_root / "src" / "app" / "social" / "page.tsx").write_text(
        'import { Header } from "@/components/Header";\nexport default Header;\n',
        encoding="utf-8",
    )

    analysis = RepositoryAnalyzer().analyze(tmp_path)
    edge_pairs = {(edge["from"], edge["to"]) for edge in analysis.graph_edges}
    labels = [node["label"] for node in analysis.graph_nodes]

    assert analysis.language == "TypeScript"
    assert analysis.framework == "Next.js"
    assert analysis.test_framework == "npm"
    assert analysis.verification_command == ["npm", "run", "test"]
    assert analysis.verification_workdir == "web"
    assert ("web/src/app/reports/page.tsx", "web/src/components/Header.tsx") in edge_pairs
    assert ("web/src/app/social/page.tsx", "web/src/components/Header.tsx") in edge_pairs
    assert len(labels) == len(set(labels))
