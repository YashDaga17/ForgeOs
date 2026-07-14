"""
ForgeOS SSE Event Models

All event types that flow through the Server-Sent Events stream.
The frontend derives its entire UI state from these events.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All SSE event types supported by ForgeOS."""
    REPOSITORY_UPDATE = "repository_update"
    ARCHITECTURE_UPDATE = "architecture_update"
    TERMINAL_LOG = "terminal_log"
    PLANNER_UPDATE = "planner_update"
    AGENT_UPDATE = "agent_update"
    DIFF_UPDATE = "diff_update"
    METRICS_UPDATE = "metrics_update"
    HEALTH_UPDATE = "health_update"
    BUSINESS_UPDATE = "business_update"
    PIPELINE_UPDATE = "pipeline_update"
    COMPLETED = "completed"
    ERROR = "error"
    DECISION_EVENT = "decision_event"
    REASONING_UPDATE = "reasoning_update"
    IMPACT_UPDATE = "impact_update"
    AI_ACTIVITY = "ai_activity"


class AgentName(str, Enum):
    """UI agent personas — visual representations of pipeline stages."""
    ATLAS = "Atlas"
    FORGE = "Forge"
    PULSE = "Pulse"
    SENTINEL = "Sentinel"
    NITRO = "Nitro"
    ORACLE = "Oracle"

    # Compatibility aliases for legacy orchestrator stages
    SUPERVISOR = "Atlas"
    REPOSITORY_ANALYST = "Oracle"
    PLANNER = "Oracle"
    REPAIR = "Forge"
    QA = "Pulse"
    SECURITY = "Sentinel"
    PERFORMANCE = "Nitro"
    BUSINESS = "Oracle"


class AgentStatus(str, Enum):
    """Status states for agent cards."""
    IDLE = "Idle"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    WAITING = "Waiting"


class ReasoningStatus(str, Enum):
    """Lifecycle states for observable engineering rationale."""

    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class AIActivityStatus(str, Enum):
    """Observable lifecycle for a bounded OpenAI operation."""

    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


# --- Event Payloads ---

class BaseEvent(BaseModel):
    """Base event with common fields."""
    event: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str = ""


class RepositoryUpdateEvent(BaseEvent):
    """Repository metadata after cloning/analysis."""
    event: EventType = EventType.REPOSITORY_UPDATE
    name: str = ""
    url: str = ""
    language: str = ""
    framework: str = ""
    test_framework: str = ""
    test_paths: list[str] = Field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    files: list[dict[str, Any]] = Field(default_factory=list)


class ArchitectureUpdateEvent(BaseEvent):
    """Architecture analysis results."""
    event: EventType = EventType.ARCHITECTURE_UPDATE
    summary: str = ""
    modules: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[dict[str, str]] = Field(default_factory=list)
    graph_nodes: list[dict[str, Any]] = Field(default_factory=list)
    graph_edges: list[dict[str, str]] = Field(default_factory=list)
    graph_truncated: bool = False
    entry_points: list[str] = Field(default_factory=list)


class TerminalLogEvent(BaseEvent):
    """Real subprocess output or supervisor messages."""
    event: EventType = EventType.TERMINAL_LOG
    source: str = "system"  # "pytest", "git", "supervisor", "system"
    content: str = ""
    is_error: bool = False


class PlannerUpdateEvent(BaseEvent):
    """Planner decisions and task breakdown."""
    event: EventType = EventType.PLANNER_UPDATE
    phase: str = ""
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    current_task: str = ""
    message: str = ""


class AgentUpdateEvent(BaseEvent):
    """Agent status change."""
    event: EventType = EventType.AGENT_UPDATE
    agent: AgentName
    status: AgentStatus
    message: str = ""
    progress: int = 0  # 0-100
    confidence: float = 0.0  # 0.0-1.0


class DiffUpdateEvent(BaseEvent):
    """Code diff from repair."""
    event: EventType = EventType.DIFF_UPDATE
    file_path: str = ""
    diff: str = ""
    explanation: str = ""
    confidence: float = 0.0
    risk: str = "low"  # low, medium, high


class MetricsUpdateEvent(BaseEvent):
    """Test and code metrics."""
    event: EventType = EventType.METRICS_UPDATE
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    test_status: str = "not_run"
    test_command: str = ""
    test_error: str = ""
    coverage: float = 0.0
    issues_found: int = 0
    issues_fixed: int = 0


class HealthUpdateEvent(BaseEvent):
    """Repository health scoring."""
    event: EventType = EventType.HEALTH_UPDATE
    overall_score: float = 0.0
    dimensions: dict[str, float] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    repository_grade: str = "Pending"
    engineering_quality: str = "Not assessed"
    business_risk: str = "Unknown"
    critical_findings: int = 0
    top_recommendation: str = ""
    deployment_recommendation: str = ""
    estimated_time_saved: str = ""
    executive_summary: str = ""


class BusinessUpdateEvent(BaseEvent):
    """Business intelligence data."""
    event: EventType = EventType.BUSINESS_UPDATE
    stars: int = 0
    forks: int = 0
    contributors: int = 0
    open_issues: int = 0
    watchers: int = 0
    release_cadence: str = ""
    dependency_health: str = ""
    community_activity: str = ""
    executive_summary: str = ""
    source: str = "local"
    repository_owner: str = ""
    repository_name: str = ""
    primary_language: str = ""
    license: str = ""
    topics: list[str] = Field(default_factory=list)
    competitor_snapshot: list[dict[str, Any]] = Field(default_factory=list)
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


class PipelineUpdateEvent(BaseEvent):
    """Pipeline stage progression."""
    event: EventType = EventType.PIPELINE_UPDATE
    stage: str = ""
    stage_index: int = 0
    total_stages: int = 14
    status: str = ""
    message: str = ""


class CompletedEvent(BaseEvent):
    """Pipeline completion."""
    event: EventType = EventType.COMPLETED
    success: bool = True
    requires_review: bool = False
    duration_seconds: float = 0.0
    summary: str = ""


class ErrorEvent(BaseEvent):
    """Pipeline error."""
    event: EventType = EventType.ERROR
    error: str = ""
    stage: str = ""
    recoverable: bool = False


class DecisionEvent(BaseEvent):
    """Structured decision reasoning event emitted by the Decision Engine."""
    event: EventType = EventType.DECISION_EVENT
    stage: str
    agent: AgentName
    reason: str
    evidence: str
    action_taken: str
    expected_outcome: str | None = None
    confidence: float
    status: str


class ReasoningUpdateEvent(BaseEvent):
    """Observable rationale for an engineering action, separate from pipeline history."""

    event: EventType = EventType.REASONING_UPDATE
    step_id: str
    stage: str
    phase: str
    title: str
    detail: str
    status: ReasoningStatus
    agent: AgentName
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ImpactUpdateEvent(BaseEvent):
    """Deterministic graph impact for an observed repair target."""

    event: EventType = EventType.IMPACT_UPDATE
    focus_files: list[str] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)
    inbound_dependents: int = 0
    outbound_dependencies: int = 0
    risk: str = "low"
    message: str = ""


class AIActivityEvent(BaseEvent):
    """Telemetry for a real OpenAI request without exposing prompt contents."""

    event: EventType = EventType.AI_ACTIVITY
    operation_id: str = ""
    capability: str = ""
    agent: AgentName | None = None
    status: AIActivityStatus = AIActivityStatus.BLOCKED
    model: str = ""
    message: str = ""
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
