"""Generates and bundles session execution summaries and JSON telemetry artifacts."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.pipeline.state import PipelineContext

logger = logging.getLogger(__name__)

class SessionArtifactManager:
    """Writes report summaries and JSON files into a session run directory."""

    def __init__(self, workspace_path: str | Path) -> None:
        self.workspace_path = Path(workspace_path)
        # Parent of backend directory is the repository workspace root
        self.project_root = self.workspace_path.parents[2]

    def generate_bundle(self, ctx: PipelineContext) -> Path | None:
        """Saves summary report, unified patch, and telemetry json files."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        run_dir_name = f"run-{date_str}-{ctx.session_id}"
        run_dir = self.project_root / "runs" / run_dir_name

        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[SessionArtifactManager] Initialized runs bundle at {run_dir}")

            # 1. Generate summary.md
            summary_path = run_dir / "summary.md"
            self._write_summary_md(summary_path, ctx)

            # 2. Generate diff.patch
            diff_path = run_dir / "diff.patch"
            self._write_diff_patch(diff_path, ctx)

            # 3. Generate health.json
            health_path = run_dir / "health.json"
            self._write_health_json(health_path, ctx)

            # 4. Generate timeline.json
            timeline_path = run_dir / "timeline.json"
            self._write_timeline_json(timeline_path, ctx)

            # 5. Generate business.json
            business_path = run_dir / "business.json"
            self._write_business_json(business_path, ctx)

            # 6. Generate architecture.json
            arch_path = run_dir / "architecture.json"
            self._write_architecture_json(arch_path, ctx)

            logger.info(f"[SessionArtifactManager] Bundle completed successfully.")
            return run_dir
        except Exception as exc:
            logger.error(f"[SessionArtifactManager] Failed to compile bundle: {exc}")
            return None

    def _write_summary_md(self, path: Path, ctx: PipelineContext) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        exec_summary = ctx.health_exec_summary
        grade = ctx.health_grade
        quality = ctx.health_quality
        risk = ctx.health_risk
        time_saved = ctx.health_time_saved
        top_rec = ctx.health_top_rec
        deploy_rec = ctx.health_deploy_rec

        recommendations_md = "\n".join(f"- {rec}" for rec in ctx.health_recommendations) or "- None"

        applied_patches = []
        for idx, item in enumerate(ctx.diffs, 1):
            applied_patches.append(
                f"### Patch {idx}: {item.get('file_path')}\n"
                f"- **Confidence**: {float(item.get('confidence', 1.0))*100:.0f}%\n"
                f"- **Risk Level**: {item.get('risk')}\n"
                f"- **Reasoning**: {item.get('explanation')}\n"
            )
        patches_summary = "\n".join(applied_patches) or "*No code patches were required or applied.*"

        content = f"""# ForgeOS Run Summary Report

**Session ID**: `{ctx.session_id}`
**Repository**: `{ctx.repo_name}` (`{ctx.repository_url}`)
**Generated At**: `{timestamp}`
**Execution Duration**: `{ctx.duration_seconds:.1f} seconds`
**Pipeline Status**: `{"SUCCESS" if ctx.success else "FAILED"}`

---

## 📝 Executive Summary
{exec_summary}

---

## 📊 Repository Health
- **Overall Score**: {ctx.health_score:.0%}
- **Grade**: `{grade}`
- **Engineering Quality**: `{quality}`
- **Business Risk**: `{risk}`
- **Deployment Recommendation**: `{deploy_rec}`
- **Estimated Time Saved**: `{time_saved}`

### Action Recommendations
{recommendations_md}

---

## 🧪 Test Suite Summary
- **Total Tests**: {ctx.tests_total}
- **Passed**: {ctx.tests_passed}
- **Failed**: {ctx.tests_failed}
- **Skipped**: {ctx.tests_skipped}
- **Defects Detected**: {ctx.issues_found}
- **Defects Fixed**: {ctx.issues_fixed}

---

## 🛠️ Applied Patches
{patches_summary}
"""
        path.write_text(content.strip(), encoding="utf-8")

    def _write_diff_patch(self, path: Path, ctx: PipelineContext) -> None:
        patches_list = []
        for idx, item in enumerate(ctx.diffs, 1):
            patches_list.append(
                f"# Patch {idx} | File: {item.get('file_path')} | Confidence: {item.get('confidence')}\n"
                f"{item.get('diff')}\n"
            )
        diff_content = "\n".join(patches_list)
        path.write_text(diff_content or "# No patches applied.", encoding="utf-8")

    def _write_health_json(self, path: Path, ctx: PipelineContext) -> None:
        data = {
            "health_score": ctx.health_score,
            "dimensions": ctx.health_dimensions,
            "recommendations": ctx.health_recommendations,
            "grade": ctx.health_grade,
            "quality": ctx.health_quality,
            "risk": ctx.health_risk,
            "critical_findings": ctx.health_findings,
            "top_recommendation": ctx.health_top_rec,
            "deployment_recommendation": ctx.health_deploy_rec,
            "estimated_time_saved": ctx.health_time_saved,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _write_timeline_json(self, path: Path, ctx: PipelineContext) -> None:
        data = {
            "session_id": ctx.session_id,
            "duration_seconds": ctx.duration_seconds,
            "completed_stages": [stage.value for stage in ctx.completed_stages],
            "errors": ctx.errors,
            "success": ctx.success,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _write_business_json(self, path: Path, ctx: PipelineContext) -> None:
        path.write_text(json.dumps(ctx.business_data, indent=2), encoding="utf-8")

    def _write_architecture_json(self, path: Path, ctx: PipelineContext) -> None:
        data = {
            "summary": ctx.architecture_summary,
            "modules": ctx.modules,
            "dependencies": ctx.dependencies,
            "graph_nodes": ctx.graph_nodes,
            "graph_edges": ctx.graph_edges,
            "graph_truncated": ctx.graph_truncated,
            "impact": ctx.impact_data,
            "entry_points": ctx.entry_points,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
