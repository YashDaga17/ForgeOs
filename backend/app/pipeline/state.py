"""
ForgeOS Pipeline State Machine

Defines pipeline stages and the execution context that flows through them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.patch_manager import PatchManager


class PipelineStage(str, Enum):
    """The 14 stages of the ForgeOS orchestration pipeline."""
    CLONE_REPOSITORY = "Clone Repository"
    ANALYZE_REPOSITORY = "Analyze Repository"
    DETECT_FRAMEWORK = "Detect Framework & Tests"
    RUN_TESTS = "Run Tests"
    CLASSIFY_FAILURES = "Classify Failures"
    DETERMINISTIC_FIX = "Try Deterministic Fixes"
    AI_REPAIR = "AI Repair"
    APPLY_PATCH = "Apply Patch"
    RERUN_TESTS = "Re-run Tests"
    MUTATION_CHECK = "Mutation Check"
    REGRESSION_TEST = "Generate Regression Test"
    CALCULATE_HEALTH = "Calculate Repository Health"
    BUSINESS_INTELLIGENCE = "Publish Business Intelligence"
    STREAM_RESULTS = "Stream Final Results"


PIPELINE_STAGES: list[PipelineStage] = list(PipelineStage)


@dataclass
class PipelineContext:
    """
    Mutable context that flows through the pipeline.
    Each stage reads from and writes to this context.
    """
    session_id: str = ""
    repository_url: str = ""
    workspace_path: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Repository info
    repo_name: str = ""
    language: str = ""
    framework: str = ""
    test_framework: str = ""
    test_paths: list[str] = field(default_factory=list)
    verification_command: list[str] = field(default_factory=list)
    verification_workdir: str = ""
    total_files: int = 0
    total_lines: int = 0
    files: list[dict[str, Any]] = field(default_factory=list)

    # Architecture
    modules: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    graph_nodes: list[dict[str, Any]] = field(default_factory=list)
    graph_edges: list[dict[str, str]] = field(default_factory=list)
    graph_truncated: bool = False
    entry_points: list[str] = field(default_factory=list)
    architecture_summary: str = ""

    # Test results
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    test_status: str = "not_run"
    test_command: str = ""
    test_error: str = ""
    test_warning: str = ""
    test_missing_dependencies: list[str] = field(default_factory=list)
    test_output: str = ""
    failures: list[dict[str, Any]] = field(default_factory=list)
    repair_failures: list[dict[str, Any]] = field(default_factory=list)

    # Repair
    diffs: list[dict[str, Any]] = field(default_factory=list)
    issues_found: int = 0
    issues_fixed: int = 0
    impact_data: dict[str, Any] = field(default_factory=dict)
    generated_regression_test: dict[str, Any] | None = None
    patch_manager: PatchManager | None = None

    # Health
    health_score: float = 0.0
    health_dimensions: dict[str, float] = field(default_factory=dict)
    health_recommendations: list[str] = field(default_factory=list)
    health_grade: str = "Pending"
    health_quality: str = "Not assessed"
    health_risk: str = "Unknown"
    health_findings: int = 0
    health_top_rec: str = "No evidence-backed recommendation was generated."
    health_deploy_rec: str = "Awaiting verification."
    health_time_saved: str = "Not estimated."
    health_exec_summary: str = "Analysis did not reach a verified completion state."

    # Business
    business_data: dict[str, Any] = field(default_factory=dict)

    # Pipeline state
    current_stage: PipelineStage | None = None
    completed_stages: list[PipelineStage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = False

    @property
    def duration_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()
