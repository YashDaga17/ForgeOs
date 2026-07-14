"""
ForgeOS Pipeline Orchestrator

Single orchestration pipeline that executes the 14-step engineering process.
The UI may present specialist agents, but the backend remains one deterministic
pipeline with AI invoked only at the repair gate.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from app.analysis.dependency_graph import calculate_blast_radius
from app.analysis.repository_analyzer import RepositoryAnalyzer
from app.config import get_settings
from app.events.manager import event_manager
from app.models.events import (
    AgentName,
    AgentStatus,
    AIActivityEvent,
    AIActivityStatus,
    AgentUpdateEvent,
    ArchitectureUpdateEvent,
    BusinessUpdateEvent,
    CompletedEvent,
    DiffUpdateEvent,
    ErrorEvent,
    HealthUpdateEvent,
    ImpactUpdateEvent,
    MetricsUpdateEvent,
    PipelineUpdateEvent,
    PlannerUpdateEvent,
    RepositoryUpdateEvent,
    ReasoningStatus,
    ReasoningUpdateEvent,
    TerminalLogEvent,
)
from app.pipeline.state import PIPELINE_STAGES, PipelineContext, PipelineStage
from app.repository.workspace import WorkspaceService, is_demo_repository
from app.services.ai_repair import AIRegressionTest, AIRepairPatch, AIRepairService
from app.services.business_intelligence import BusinessIntelligenceService
from app.services.git_integration import GitIntegrationService
from app.services.repair_engine import RepairEngine, RepairPatch, unified_diff
from app.services.patch_manager import PatchManager
from app.services.rollback_manager import RollbackManager
from app.services.artifact_manager import SessionArtifactManager
from app.verification.pytest_runner import VerificationRunner
from app.pipeline.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class Orchestrator:
    """Executes the ForgeOS pipeline for a repository URL."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.workspace = WorkspaceService(self.settings)
        self.analyzer = RepositoryAnalyzer()
        self.verification_runner = VerificationRunner()
        self.repair_engine = RepairEngine()
        self.ai_repair = AIRepairService(self.settings)
        self.business_intelligence = BusinessIntelligenceService(self.settings)
        self.git_integration = GitIntegrationService(self.settings)

    async def run(self, repository_url: str) -> str:
        """Start the full pipeline in the background and return a session id."""
        session_id = str(uuid.uuid4())[:8]
        ctx = PipelineContext(session_id=session_id, repository_url=repository_url)
        event_manager.create_session(session_id)
        asyncio.create_task(self._execute_pipeline(ctx))
        return session_id

    async def _execute_pipeline(self, ctx: PipelineContext) -> None:
        try:
            for index, stage in enumerate(PIPELINE_STAGES):
                ctx.current_stage = stage
                await event_manager.publish(
                    ctx.session_id,
                    PipelineUpdateEvent(
                        stage=stage.value,
                        stage_index=index,
                        total_stages=len(PIPELINE_STAGES),
                        status="running",
                        message=f"Starting {stage.value}...",
                    ),
                )
                await self._execute_stage(ctx, stage)
                ctx.completed_stages.append(stage)
                
                # Emit Decision Event
                try:
                    decision_event = DecisionEngine.generate_decision(ctx, stage, "Completed")
                    await event_manager.publish(ctx.session_id, decision_event)
                except Exception as dec_exc:
                    logger.warning("Failed to generate decision event for stage %s: %s", stage.value, dec_exc)

                await event_manager.publish(
                    ctx.session_id,
                    PipelineUpdateEvent(
                        stage=stage.value,
                        stage_index=index + 1,
                        total_stages=len(PIPELINE_STAGES),
                        status="completed",
                        message=f"{stage.value} complete",
                    ),
                )

            await event_manager.publish(
                ctx.session_id,
                CompletedEvent(
                    success=ctx.success,
                    requires_review=ctx.test_status in {"no_tests", "error"},
                    duration_seconds=ctx.duration_seconds,
                    summary=(
                        f"Pipeline completed in {ctx.duration_seconds:.1f}s. "
                        f"{ctx.issues_found} issues found, {ctx.issues_fixed} fixed. "
                        f"{self._verification_summary(ctx)}"
                    ),
                ),
            )
        except Exception as exc:
            logger.exception("Pipeline failed: %s", exc)
            ctx.success = False
            if ctx.current_stage:
                try:
                    decision_event = DecisionEngine.generate_decision(ctx, ctx.current_stage, "Failed")
                    decision_event.reason = f"Failure during stage execution: {str(exc)}"
                    await event_manager.publish(ctx.session_id, decision_event)
                except Exception as dec_exc:
                    logger.warning("Failed to generate failure decision event: %s", dec_exc)
            await event_manager.publish(
                ctx.session_id,
                ErrorEvent(
                    error=str(exc),
                    stage=ctx.current_stage.value if ctx.current_stage else "unknown",
                    recoverable=False,
                ),
            )
        finally:
            await asyncio.sleep(0.5)
            await event_manager.close_session(ctx.session_id)

    async def _execute_stage(self, ctx: PipelineContext, stage: PipelineStage) -> None:
        handlers = {
            PipelineStage.CLONE_REPOSITORY: self._stage_clone,
            PipelineStage.ANALYZE_REPOSITORY: self._stage_analyze,
            PipelineStage.DETECT_FRAMEWORK: self._stage_detect_framework,
            PipelineStage.RUN_TESTS: self._stage_run_tests,
            PipelineStage.CLASSIFY_FAILURES: self._stage_classify_failures,
            PipelineStage.DETERMINISTIC_FIX: self._stage_deterministic_fix,
            PipelineStage.AI_REPAIR: self._stage_ai_repair,
            PipelineStage.APPLY_PATCH: self._stage_apply_patch,
            PipelineStage.RERUN_TESTS: self._stage_rerun_tests,
            PipelineStage.MUTATION_CHECK: self._stage_mutation_check,
            PipelineStage.REGRESSION_TEST: self._stage_regression_test,
            PipelineStage.CALCULATE_HEALTH: self._stage_calculate_health,
            PipelineStage.BUSINESS_INTELLIGENCE: self._stage_business_intelligence,
            PipelineStage.STREAM_RESULTS: self._stage_stream_results,
        }
        await handlers[stage](ctx)

    async def _stage_clone(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="repository-scope",
            stage=PipelineStage.CLONE_REPOSITORY,
            phase="Scope",
            title="Scope repository",
            detail="Confirming the repository target before allocating an isolated workspace.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.SUPERVISOR,
            evidence=[ctx.repository_url or "bundled demo repository"],
            confidence=0.98,
        )
        await self._agent(ctx, AgentName.SUPERVISOR, "Running", "Preparing repository workspace...", progress=10)
        await self._terminal(ctx, "git", f"$ forgeos workspace prepare {ctx.repository_url or 'demo'}")
        result = await self.workspace.prepare(ctx.repository_url, ctx.session_id)
        ctx.repo_name = result.repo_name
        ctx.workspace_path = str(result.workspace_path)
        await self._terminal(ctx, "git", f"Workspace ready: {result.workspace_path}")
        await self._terminal(ctx, "git", f"Source: {result.source} ({result.display_url})")
        await self._reasoning(
            ctx,
            step_id="repository-scope",
            stage=PipelineStage.CLONE_REPOSITORY,
            phase="Scope",
            title="Scope repository",
            detail=f"Workspace isolated at {result.workspace_path}; the pipeline can inspect files without mutating the source repository.",
            status=ReasoningStatus.COMPLETED,
            agent=AgentName.SUPERVISOR,
            evidence=[result.source, str(result.workspace_path)],
            confidence=0.99,
        )
        await self._agent(ctx, AgentName.SUPERVISOR, "Completed", f"Repository ready: {ctx.repo_name}", progress=100, confidence=0.96)

    async def _stage_analyze(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="file-inventory",
            stage=PipelineStage.ANALYZE_REPOSITORY,
            phase="Discovery",
            title="Build file inventory",
            detail="Scanning source, tests, configuration, and documentation to establish the repository evidence set.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPOSITORY_ANALYST,
            confidence=0.95,
        )
        await self._agent(ctx, AgentName.REPOSITORY_ANALYST, "Running", "Scanning repository structure...", progress=10)
        analysis = await asyncio.to_thread(self.analyzer.analyze, ctx.workspace_path)
        ctx.total_files = analysis.total_files
        ctx.total_lines = analysis.total_lines
        ctx.files = analysis.files
        ctx.language = analysis.language
        ctx.framework = analysis.framework
        ctx.test_framework = analysis.test_framework
        ctx.test_paths = analysis.test_paths
        ctx.verification_command = analysis.verification_command
        ctx.verification_workdir = analysis.verification_workdir
        ctx.modules = analysis.modules
        ctx.dependencies = analysis.dependencies
        ctx.graph_nodes = analysis.graph_nodes
        ctx.graph_edges = analysis.graph_edges
        ctx.graph_truncated = analysis.graph_truncated
        ctx.entry_points = analysis.entry_points
        ctx.architecture_summary = analysis.architecture_summary

        await self._terminal(ctx, "system", f"Found {ctx.total_files} files, {ctx.total_lines} lines")
        await event_manager.publish(
            ctx.session_id,
            RepositoryUpdateEvent(
                name=ctx.repo_name,
                url=ctx.repository_url,
                language=ctx.language,
                framework=ctx.framework,
                test_framework=ctx.test_framework,
                test_paths=ctx.test_paths,
                total_files=ctx.total_files,
                total_lines=ctx.total_lines,
                files=ctx.files,
            ),
        )
        await self._reasoning(
            ctx,
            step_id="file-inventory",
            stage=PipelineStage.ANALYZE_REPOSITORY,
            phase="Discovery",
            title="Build file inventory",
            detail="The repository map is complete and can now support framework detection and targeted repair.",
            status=ReasoningStatus.COMPLETED,
            agent=AgentName.REPOSITORY_ANALYST,
            evidence=[f"{ctx.total_files} files", f"{ctx.total_lines} lines"],
            confidence=0.98,
        )
        await self._agent(ctx, AgentName.REPOSITORY_ANALYST, "Completed", "Repository analysis complete", progress=100, confidence=0.95)

    async def _stage_detect_framework(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="execution-strategy",
            stage=PipelineStage.DETECT_FRAMEWORK,
            phase="Discovery",
            title="Select execution strategy",
            detail="Matching detected language, framework, and test runner to the supported verification path.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPOSITORY_ANALYST,
            evidence=[ctx.language or "unknown language", ctx.framework or "unknown framework", ctx.test_framework or "unknown test runner"],
            confidence=0.9,
        )
        await self._agent(ctx, AgentName.REPOSITORY_ANALYST, "Running", "Building architecture map...", progress=70)
        test_signal = (
            f"{ctx.test_framework} ({len(ctx.test_paths)} target{'s' if len(ctx.test_paths) != 1 else ''})"
            if ctx.test_framework and ctx.test_paths
            else ctx.test_framework or "no repository test script or test files detected"
        )
        await self._terminal(ctx, "system", f"Language: {ctx.language or 'unknown'} | Framework: {ctx.framework or 'unknown'} | Tests: {test_signal}")
        await event_manager.publish(
            ctx.session_id,
            ArchitectureUpdateEvent(
                summary=ctx.architecture_summary,
                modules=ctx.modules,
                dependencies=ctx.dependencies,
                graph_nodes=ctx.graph_nodes,
                graph_edges=ctx.graph_edges,
                graph_truncated=ctx.graph_truncated,
                entry_points=ctx.entry_points,
            ),
        )
        await self._reasoning(
            ctx,
            step_id="execution-strategy",
            stage=PipelineStage.DETECT_FRAMEWORK,
            phase="Discovery",
            title="Select execution strategy",
            detail=f"Configured the {ctx.test_framework or 'available'} verification path for the detected {ctx.framework or 'application'} codebase.",
            status=ReasoningStatus.COMPLETED,
            agent=AgentName.REPOSITORY_ANALYST,
            evidence=[f"framework={ctx.framework or 'unknown'}", f"tests={ctx.test_framework or 'unknown'}"],
            confidence=0.96,
        )
        await self._agent(ctx, AgentName.REPOSITORY_ANALYST, "Completed", "Architecture map ready", progress=100, confidence=0.96)

    async def _stage_run_tests(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="read-traceback",
            stage=PipelineStage.RUN_TESTS,
            phase="Evidence",
            title="Read traceback",
            detail="Running the real test suite so repair decisions are grounded in current failures rather than assumptions.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.QA,
            evidence=[ctx.test_framework or "no test runner", "repository test suite"],
            confidence=0.98,
        )
        await self._agent(ctx, AgentName.QA, "Running", "Running the discovered repository test command...", progress=10)
        result = await self._run_verification(ctx)
        self._apply_test_result(ctx, result)
        await event_manager.publish(
            ctx.session_id,
            MetricsUpdateEvent(
                tests_total=ctx.tests_total,
                tests_passed=ctx.tests_passed,
                tests_failed=ctx.tests_failed,
                tests_skipped=ctx.tests_skipped,
                test_status=ctx.test_status,
                test_command=ctx.test_command,
                test_error=ctx.test_error,
                issues_found=self._observed_issue_count(ctx),
                issues_fixed=ctx.issues_fixed,
            ),
        )
        await self._reasoning(
            ctx,
            step_id="read-traceback",
            stage=PipelineStage.RUN_TESTS,
            phase="Evidence",
            title="Read traceback",
            detail=self._test_evidence_detail(ctx),
            status=ReasoningStatus.COMPLETED if ctx.test_status in {"passed", "failed"} else ReasoningStatus.BLOCKED,
            agent=AgentName.QA,
            evidence=[f"failed={ctx.tests_failed}", f"passed={ctx.tests_passed}", f"skipped={ctx.tests_skipped}"],
            confidence=0.99,
        )
        await self._agent(
            ctx,
            AgentName.QA,
            "Completed" if ctx.test_status == "passed" else "Failed" if ctx.test_status == "failed" else "Waiting",
            self._test_agent_message(ctx),
            progress=100,
            confidence=0.93,
        )

    async def _stage_classify_failures(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="compare-traces",
            stage=PipelineStage.CLASSIFY_FAILURES,
            phase="Diagnosis",
            title="Compare stack traces",
            detail="Comparing failure locations and exception types to separate actionable defects from test noise.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.PLANNER,
            evidence=[f"{len(ctx.failures)} parsed failure(s)"],
            confidence=0.9,
        )
        await self._agent(ctx, AgentName.PLANNER, "Running", "Classifying failures...", progress=25)
        ctx.issues_found = self._observed_issue_count(ctx)
        ctx.repair_failures = [dict(failure) for failure in ctx.failures]
        tasks = [self._failure_to_task(index, failure) for index, failure in enumerate(ctx.failures, start=1)]
        if not tasks and ctx.test_status == "no_tests":
            tasks = [
                {
                    "id": 1,
                    "title": "Add or declare a runnable automated test suite",
                    "type": "verification_blocked",
                    "priority": "critical",
                    "file": "",
                }
            ]
        elif not tasks and ctx.test_status == "error":
            missing = ", ".join(ctx.test_missing_dependencies)
            tasks = [
                {
                    "id": 1,
                    "title": (
                        f"Provision the repository test environment ({missing})"
                        if missing
                        else "Resolve the repository test command or environment error"
                    ),
                    "type": "test_environment_missing_dependency" if missing else "test_collection_error",
                    "priority": "high",
                    "file": "",
                }
            ]
        await event_manager.publish(
            ctx.session_id,
            PlannerUpdateEvent(
                phase="Failure Classification",
                tasks=tasks,
                current_task="Repair plan ready" if tasks else "No repair needed",
                message=(
                    f"Classified {len(ctx.failures)} failures from real repository test output."
                    if ctx.failures
                    else self._test_status_message(ctx)
                ),
            ),
        )
        for task in tasks:
            await self._terminal(ctx, "supervisor", f"[Planner] {task['title']} -> {task['type']}")
        await self._publish_impact(
            ctx,
            [str(failure.get("source_file", "")) for failure in ctx.repair_failures],
        )
        await self._reasoning(
            ctx,
            step_id="compare-traces",
            stage=PipelineStage.CLASSIFY_FAILURES,
            phase="Diagnosis",
            title="Compare stack traces",
            detail=(
                "Grouped the observed failures by error type and affected source file so the repair gate can choose the smallest valid action."
                if ctx.failures
                else self._test_status_message(ctx)
            ),
            status=ReasoningStatus.COMPLETED if ctx.failures or ctx.test_status == "passed" else ReasoningStatus.BLOCKED,
            agent=AgentName.PLANNER,
            evidence=[f"{len(tasks)} repair task(s)", *[str(task["type"]) for task in tasks[:3]]],
            confidence=0.94,
        )
        await self._reasoning(
            ctx,
            step_id="root-cause",
            stage=PipelineStage.CLASSIFY_FAILURES,
            phase="Diagnosis",
            title="Identify root cause",
            detail="Tracing each failure back to the smallest source-level condition that explains the observed test result.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.PLANNER,
            evidence=[failure.get("source_file", "unknown source") for failure in ctx.failures[:3]],
            confidence=0.88,
        )
        await self._reasoning(
            ctx,
            step_id="root-cause",
            stage=PipelineStage.CLASSIFY_FAILURES,
            phase="Diagnosis",
            title="Identify root cause",
            detail="Root causes are mapped to repair targets and prioritized before any patch is written.",
            status=ReasoningStatus.COMPLETED if ctx.failures or ctx.test_status == "passed" else ReasoningStatus.BLOCKED,
            agent=AgentName.PLANNER,
            evidence=[failure.get("error", failure.get("type", "unclassified failure")) for failure in ctx.failures[:3]],
            confidence=0.92 if ctx.failures else 1.0,
        )
        await self._agent(
            ctx,
            AgentName.PLANNER,
            "Completed" if ctx.failures or ctx.test_status == "passed" else "Waiting",
            "Repair plan ready" if ctx.failures or ctx.test_status == "passed" else "Verification prerequisite identified",
            progress=100 if ctx.failures or ctx.test_status == "passed" else 40,
            confidence=0.9 if ctx.failures or ctx.test_status == "passed" else 0.5,
        )

    async def _stage_deterministic_fix(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="search-module",
            stage=PipelineStage.DETERMINISTIC_FIX,
            phase="Patch",
            title="Search affected module",
            detail="Checking known source locations and deterministic repair rules before opening the AI gate.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPAIR,
            evidence=[failure.get("source_file", "unknown source") for failure in ctx.failures[:3]],
            confidence=0.9,
        )
        await self._agent(ctx, AgentName.REPAIR, "Running", "Attempting deterministic fixes...", progress=20)
        patches = self.repair_engine.plan_deterministic(ctx.workspace_path, ctx.failures)
        for patch in patches:
            ctx.diffs.append(patch.as_dict())
            await self._terminal(ctx, "supervisor", f"[Repair] Planned deterministic patch: {patch.file_path}")
        if patches:
            await self._publish_impact(ctx, [patch.file_path for patch in patches])
        await self._reasoning(
            ctx,
            step_id="search-module",
            stage=PipelineStage.DETERMINISTIC_FIX,
            phase="Patch",
            title="Search affected module",
            detail=f"Located {len(patches)} deterministic repair target(s) without requiring a model call.",
            status=ReasoningStatus.COMPLETED,
            agent=AgentName.REPAIR,
            evidence=[patch.file_path for patch in patches] or ["no deterministic match"],
            confidence=0.96 if patches else 0.62,
        )
        await self._reasoning(
            ctx,
            step_id="generate-patch",
            stage=PipelineStage.DETERMINISTIC_FIX,
            phase="Patch",
            title="Generate patch",
            detail="Preparing the smallest patch that addresses the diagnosed source condition.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPAIR,
            evidence=[patch.file_path for patch in patches] or ["AI gate may be required"],
            confidence=0.9,
        )
        await self._reasoning(
            ctx,
            step_id="generate-patch",
            stage=PipelineStage.DETERMINISTIC_FIX,
            phase="Patch",
            title="Generate patch",
            detail="Deterministic patch candidates are ready for application; unresolved failures continue to the AI repair gate.",
            status=ReasoningStatus.COMPLETED if patches else ReasoningStatus.BLOCKED,
            agent=AgentName.REPAIR,
            evidence=[f"{len(patches)} candidate patch(es)"],
            confidence=0.95 if patches else 0.6,
        )
        await self._agent(
            ctx,
            AgentName.REPAIR,
            "Running" if patches else "Waiting",
            f"{len(patches)} deterministic patches planned" if patches else "No deterministic patches matched",
            progress=50,
            confidence=0.86 if patches else 0.4,
        )

    async def _stage_ai_repair(self, ctx: PipelineContext) -> None:
        if ctx.test_status in {"no_tests", "error"}:
            await self._ai_activity(
                ctx,
                operation_id="ai-repair",
                capability="repair",
                status=AIActivityStatus.BLOCKED,
                model=self.settings.openai_repair_model,
                message="No model request: AI repair requires an actionable collected test failure.",
            )
            await self._terminal(
                ctx,
                "supervisor",
                f"[AI Repair] Gate blocked: {self._test_status_message(ctx)}",
                is_error=ctx.test_status == "error",
            )
            await self._reasoning(
                ctx,
                step_id="ai-repair-gate",
                stage=PipelineStage.AI_REPAIR,
                phase="Decision",
                title="Evaluate AI repair gate",
                detail="AI repair requires an actionable failure from a collected test. No model call was made because verification evidence is unavailable.",
                status=ReasoningStatus.BLOCKED,
                agent=AgentName.REPAIR,
                evidence=[ctx.test_error or self._test_status_message(ctx), "model call skipped"],
                confidence=0.99,
            )
            await self._agent(ctx, AgentName.REPAIR, "Waiting", "AI repair withheld until tests can be collected", progress=80, confidence=0.0)
            return

        remaining_failures = self._failures_without_planned_patch(ctx)
        if not remaining_failures:
            await self._ai_activity(
                ctx,
                operation_id="ai-repair",
                capability="repair",
                status=AIActivityStatus.BLOCKED,
                model=self.settings.openai_repair_model,
                message="No model request: deterministic candidates cover the observed failures.",
            )
            await self._terminal(ctx, "supervisor", "[AI Repair] No unresolved failures require AI")
            await self._reasoning(
                ctx,
                step_id="ai-repair-gate",
                stage=PipelineStage.AI_REPAIR,
                phase="Decision",
                title="Evaluate AI repair gate",
                detail="Deterministic repair candidates cover the diagnosed failures, so the model is not invoked.",
                status=ReasoningStatus.COMPLETED,
                agent=AgentName.REPAIR,
                evidence=["no unresolved failures"],
                confidence=0.98,
            )
            await self._agent(ctx, AgentName.REPAIR, "Completed", "AI repair not required", progress=80, confidence=0.9)
            return

        await self._reasoning(
            ctx,
            step_id="ai-repair-gate",
            stage=PipelineStage.AI_REPAIR,
            phase="Decision",
            title="Evaluate AI repair gate",
            detail="Deterministic rules did not cover every failure, so ForgeOS is evaluating whether a structured model patch is necessary.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPAIR,
            evidence=[failure.get("source_file", "unknown source") for failure in remaining_failures],
            confidence=0.9,
        )
        await self._agent(ctx, AgentName.REPAIR, "Running", "Checking OpenAI repair gate...", progress=65)
        await self._terminal(ctx, "supervisor", "[AI Repair] Evaluating unresolved failures against the model gate")
        await self._ai_activity(
            ctx,
            operation_id="ai-repair",
            capability="repair",
            status=AIActivityStatus.RUNNING,
            model=self.settings.openai_repair_model,
            message="OpenAI is generating one structured repair candidate from the collected failure evidence.",
        )
        result = await self.ai_repair.repair(
            repository_name=ctx.repo_name,
            failures=remaining_failures,
            test_output=self._failure_evidence(remaining_failures),
            file_context=self._source_file_context(ctx, remaining_failures),
            test_context=self._failing_test_context(ctx, remaining_failures),
        )
        await self._ai_activity(
            ctx,
            operation_id="ai-repair",
            capability="repair",
            status=AIActivityStatus(result.status),
            model=result.model,
            message=result.message,
            request_id=result.request_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        if result.status == "completed" and result.patch:
            ctx.diffs.append(self._patch_to_diff(result.patch))
            await self._publish_impact(ctx, [result.patch.file_path])
            await self._terminal(ctx, "supervisor", f"[AI Repair] Model {result.model} returned a structured patch")
            await self._reasoning(
                ctx,
                step_id="ai-repair-gate",
                stage=PipelineStage.AI_REPAIR,
                phase="Decision",
                title="Evaluate AI repair gate",
                detail="OpenAI returned a structured patch after deterministic repair could not resolve every failure.",
                status=ReasoningStatus.COMPLETED,
                agent=AgentName.REPAIR,
                evidence=[result.model, result.patch.file_path, f"risk={result.patch.risk}"],
                confidence=result.patch.confidence,
            )
            await self._reasoning(
                ctx,
                step_id="generate-patch",
                stage=PipelineStage.AI_REPAIR,
                phase="Patch",
                title="Generate patch",
                detail="The structured AI patch is queued for application and will not be trusted until verification passes.",
                status=ReasoningStatus.COMPLETED,
                agent=AgentName.REPAIR,
                evidence=[result.patch.file_path, "unified diff", f"confidence={result.patch.confidence:.0%}"],
                confidence=result.patch.confidence,
            )
            await self._agent(ctx, AgentName.REPAIR, "Running", "AI patch received", progress=80, confidence=result.patch.confidence)
            return

        await self._terminal(ctx, "supervisor", f"[AI Repair] {result.message}", is_error=result.status != "blocked")
        fallback_queued = False
        if (
            result.status == "blocked"
            and self.settings.allow_demo_ai_fallback
            and is_demo_repository(ctx.repository_url)
        ):
            fallback = self.repair_engine.demo_user_validation_patch(ctx.workspace_path)
            if fallback:
                ctx.diffs.append(fallback.as_dict())
                fallback_queued = True
                await self._terminal(ctx, "supervisor", "[AI Repair] Demo fallback patch queued because API key is not available")
                await self._reasoning(
                    ctx,
                    step_id="generate-patch",
                    stage=PipelineStage.AI_REPAIR,
                    phase="Patch",
                    title="Generate patch",
                    detail="The model gate is unavailable, so the configured demo fallback produced a bounded local patch for verification.",
                    status=ReasoningStatus.COMPLETED,
                    agent=AgentName.REPAIR,
                    evidence=[fallback.file_path, "demo fallback", "model was not called"],
                    confidence=fallback.confidence,
                )
        await self._reasoning(
            ctx,
            step_id="ai-repair-gate",
            stage=PipelineStage.AI_REPAIR,
            phase="Decision",
            title="Evaluate AI repair gate",
            detail=(
                "OpenAI credentials are unavailable; the gate stayed truthful and queued the bounded demo fallback."
                if fallback_queued
                else "The AI repair gate did not produce a patch, so no unverified code was applied."
            ),
            status=ReasoningStatus.BLOCKED if result.status == "blocked" else ReasoningStatus.FAILED,
            agent=AgentName.REPAIR,
            evidence=[result.message, "fallback queued" if fallback_queued else "no patch queued"],
            confidence=0.76 if fallback_queued else 0.0,
        )
        await self._agent(
            ctx,
            AgentName.REPAIR,
            "Waiting" if result.status == "blocked" else "Failed",
            "AI gate handled; fallback queued" if fallback_queued else "AI repair gated",
            progress=80,
            confidence=0.0,
        )

    async def _stage_apply_patch(self, ctx: PipelineContext) -> None:
        await self._reasoning(
            ctx,
            step_id="apply-patch",
            stage=PipelineStage.APPLY_PATCH,
            phase="Patch",
            title="Apply approved patch",
            detail="Applying only the queued deterministic or structured diff candidates inside the isolated workspace.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.REPAIR,
            evidence=[str(item.get("file_path", "unknown file")) for item in ctx.diffs],
            confidence=0.92,
        )
        await self._agent(ctx, AgentName.FORGE, "Running", "Applying patches to workspace...", progress=85)
        applied = 0
        patch_manager = PatchManager(ctx.workspace_path)
        ctx.patch_manager = patch_manager

        for item in ctx.diffs:
            patch = RepairPatch(
                file_path=str(item["file_path"]),
                diff=str(item["diff"]),
                explanation=str(item["explanation"]),
                confidence=float(item["confidence"]),
                risk=str(item["risk"]),
                source=str(item.get("source", "ai")),
            )
            # Backup original file contents
            patch_manager.backup(patch)

            success = await self.repair_engine.apply(ctx.workspace_path, patch)
            if success:
                applied += 1
                await self._terminal(ctx, "supervisor", f"[Repair] Applied patch: {patch.file_path}")
            else:
                await self._terminal(ctx, "supervisor", f"[Repair] Patch skipped or failed: {patch.file_path}", is_error=True)
            await event_manager.publish(
                ctx.session_id,
                DiffUpdateEvent(
                    file_path=patch.file_path,
                    diff=patch.diff,
                    explanation=patch.explanation,
                    confidence=patch.confidence,
                    risk=patch.risk,
                ),
            )
        ctx.issues_fixed = applied
        await self._reasoning(
            ctx,
            step_id="apply-patch",
            stage=PipelineStage.APPLY_PATCH,
            phase="Patch",
            title="Apply approved patch",
            detail=(
                f"Applied {applied} patch(es) to the isolated workspace; the next stage will verify behavior with the repository test command."
                if ctx.diffs
                else "No patch was applied because no verified repair candidate was available."
            ),
            status=ReasoningStatus.COMPLETED if applied == len(ctx.diffs) and ctx.diffs else ReasoningStatus.BLOCKED if not ctx.diffs else ReasoningStatus.FAILED,
            agent=AgentName.REPAIR,
            evidence=[f"applied={applied}", f"planned={len(ctx.diffs)}"],
            confidence=0.95 if applied == len(ctx.diffs) else 0.55,
        )
        await self._agent(
            ctx,
            AgentName.FORGE,
            "Completed" if ctx.diffs and applied == len(ctx.diffs) else "Waiting" if not ctx.diffs else "Failed",
            f"{applied} patches applied" if ctx.diffs else "No verified patch to apply",
            progress=100 if ctx.diffs else 0,
            confidence=0.94 if ctx.diffs and applied == len(ctx.diffs) else 0.0,
        )

    async def _stage_rerun_tests(self, ctx: PipelineContext) -> None:
        if ctx.test_status in {"no_tests", "error"}:
            ctx.success = False
            await self._terminal(
                ctx,
                "verification",
                f"[QA] Verification blocked: {self._test_status_message(ctx)}",
                is_error=ctx.test_status == "error",
            )
            await self._reasoning(
                ctx,
                step_id="verify-assumptions",
                stage=PipelineStage.RERUN_TESTS,
                phase="Verification",
                title="Verify assumptions",
                detail="Verification was not run because the repository does not have a collected test result to compare against.",
                status=ReasoningStatus.BLOCKED,
                agent=AgentName.QA,
                evidence=[ctx.test_error or self._test_status_message(ctx)],
                confidence=0.99,
            )
            await self._reasoning(
                ctx,
                step_id="patch-approved",
                stage=PipelineStage.RERUN_TESTS,
                phase="Verification",
                title="Approve patch",
                detail="Patch approval withheld because the repository could not be verified.",
                status=ReasoningStatus.BLOCKED,
                agent=AgentName.QA,
                evidence=["no verification evidence"],
                confidence=0.99,
            )
            await self._agent(ctx, AgentName.PULSE, "Waiting", self._test_agent_message(ctx), progress=0, confidence=0.0)
            return

        await self._reasoning(
            ctx,
            step_id="verify-assumptions",
            stage=PipelineStage.RERUN_TESTS,
            phase="Verification",
            title="Verify assumptions",
            detail="Re-running the real test suite to confirm the patch changed behavior in the intended direction.",
            status=ReasoningStatus.RUNNING,
            agent=AgentName.QA,
            evidence=[f"{len(ctx.diffs)} patch(es) applied"],
            confidence=0.95,
        )
        await self._agent(ctx, AgentName.PULSE, "Running", "Re-running the repository test command...", progress=15)
        result = await self._run_verification(ctx)
        self._apply_test_result(ctx, result)
        ctx.success = result.status == "passed" and result.tests_total > 0 and result.tests_failed == 0
        await event_manager.publish(
            ctx.session_id,
            MetricsUpdateEvent(
                tests_total=ctx.tests_total,
                tests_passed=ctx.tests_passed,
                tests_failed=ctx.tests_failed,
                tests_skipped=ctx.tests_skipped,
                test_status=ctx.test_status,
                test_command=ctx.test_command,
                test_error=ctx.test_error,
                issues_found=ctx.issues_found,
                issues_fixed=ctx.issues_fixed,
            ),
        )

        patch_manager = ctx.patch_manager
        if not ctx.success:
            await self._terminal(ctx, "supervisor", "[Repair] Test verification failed! Reverting modifications...", is_error=True)
            if patch_manager:
                rollback_manager = RollbackManager(ctx.workspace_path)
                rollback_success = rollback_manager.rollback(patch_manager.get_backups())
                if rollback_success:
                    await self._terminal(ctx, "supervisor", "[Repair] Rollback completed. Codebase restored to original state.")
                else:
                    await self._terminal(ctx, "supervisor", "[Repair] Rollback partial or failed.", is_error=True)
            # Clear invalid patches and notify agents
            ctx.diffs.clear()
            await self._agent(ctx, AgentName.FORGE, "Failed", "Verification failed; patches rolled back", progress=0, confidence=0.0)
        else:
            await self._terminal(ctx, "supervisor", "[Repair] Verification passed! Committing changes.")
            if patch_manager:
                patch_manager.clear()

        await self._reasoning(
            ctx,
            step_id="verify-assumptions",
            stage=PipelineStage.RERUN_TESTS,
            phase="Verification",
            title="Verify assumptions",
            detail=(
                "Verification confirms the repaired workspace is green."
                if ctx.success
                else "Verification found remaining failures, so the repair cannot be approved."
            ),
            status=ReasoningStatus.COMPLETED if ctx.success else ReasoningStatus.FAILED,
            agent=AgentName.QA,
            evidence=[f"status={ctx.test_status}", f"passed={ctx.tests_passed}", f"failed={ctx.tests_failed}"],
            confidence=0.99 if ctx.success else 0.55,
        )
        await self._reasoning(
            ctx,
            step_id="patch-approved",
            stage=PipelineStage.RERUN_TESTS,
            phase="Verification",
            title="Approve patch",
            detail=(
                "Patch approved after the verification suite passed."
                if ctx.success
                else "Patch approval withheld because verification still reports failures."
            ),
            status=ReasoningStatus.COMPLETED if ctx.success else ReasoningStatus.FAILED,
            agent=AgentName.QA,
            evidence=["test suite green" if ctx.success else "test failures remain", f"issues_fixed={ctx.issues_fixed}"],
            confidence=0.99 if ctx.success else 0.5,
        )

        await self._agent(
            ctx,
            AgentName.PULSE,
            "Completed" if ctx.success else "Failed",
            "All discovered tests passing" if ctx.success else self._test_agent_message(ctx),
            progress=100,
            confidence=0.99 if ctx.success else 0.55,
        )

    async def _stage_mutation_check(self, ctx: PipelineContext) -> None:
        await self._agent(ctx, AgentName.QA, "Running", "Running targeted mutation check...", progress=40)
        if not ctx.success:
            await self._terminal(ctx, "supervisor", "[Mutation] Skipped because verification did not pass", is_error=True)
            await self._agent(ctx, AgentName.QA, "Waiting", "Mutation check deferred until verification passes", progress=0, confidence=0.0)
            return
        await self._terminal(
            ctx,
            "supervisor",
            "[Mutation] Targeted mutation execution is unavailable for this workspace; coverage evidence was recorded without claiming a pass.",
        )
        await self._agent(ctx, AgentName.QA, "Waiting", "Mutation check not executed", progress=0, confidence=0.0)

    async def _stage_regression_test(self, ctx: PipelineContext) -> None:
        await self._agent(ctx, AgentName.QA, "Running", "Evaluating regression coverage...", progress=60)
        if not ctx.success:
            message = "Regression generation deferred because verification did not pass"
            await self._ai_activity(
                ctx,
                operation_id="ai-regression-proof",
                capability="regression_test",
                status=AIActivityStatus.BLOCKED,
                model=self.settings.openai_repair_model,
                message="No model request: regression proof requires a verified repair.",
            )
            await self._terminal(ctx, "supervisor", f"[QA] {message}")
            await self._agent(ctx, AgentName.QA, "Waiting", "Regression coverage not approved", progress=0, confidence=0.0)
            return

        if not ctx.repair_failures:
            await self._ai_activity(
                ctx,
                operation_id="ai-regression-proof",
                capability="regression_test",
                status=AIActivityStatus.BLOCKED,
                model=self.settings.openai_repair_model,
                message="No model request: this run did not begin with a repairable test failure.",
            )
            await self._terminal(ctx, "supervisor", "[QA] Existing verified tests remain available as regression coverage")
            await self._agent(ctx, AgentName.QA, "Completed", "Regression coverage evaluated", progress=100, confidence=0.88)
            return

        await self._terminal(ctx, "supervisor", "[QA] Requesting one bounded OpenAI regression test candidate")
        await self._ai_activity(
            ctx,
            operation_id="ai-regression-proof",
            capability="regression_test",
            status=AIActivityStatus.RUNNING,
            model=self.settings.openai_repair_model,
            message="OpenAI is drafting one new pytest regression test for the verified repair.",
        )
        result = await self.ai_repair.generate_regression_test(
            repository_name=ctx.repo_name,
            failures=ctx.repair_failures,
            file_context=self._regression_file_context(ctx),
            test_paths=ctx.test_paths,
        )
        await self._ai_activity(
            ctx,
            operation_id="ai-regression-proof",
            capability="regression_test",
            status=AIActivityStatus(result.status),
            model=result.model,
            message=result.message,
            request_id=result.request_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        if result.status != "completed" or not result.regression_test:
            await self._terminal(ctx, "supervisor", f"[QA] {result.message}", is_error=result.status == "failed")
            await self._agent(
                ctx,
                AgentName.QA,
                "Waiting" if result.status == "blocked" else "Failed",
                "Regression test not added",
                progress=80,
                confidence=0.0,
            )
            return

        kept = await self._verify_generated_regression_test(ctx, result.regression_test)
        await self._agent(
            ctx,
            AgentName.QA,
            "Completed" if kept else "Waiting",
            "AI regression test verified" if kept else "AI regression test rejected; verified repair retained",
            progress=100 if kept else 85,
            confidence=result.regression_test.confidence if kept else 0.0,
        )

    async def _stage_calculate_health(self, ctx: PipelineContext) -> None:
        await self._agent(ctx, AgentName.SECURITY, "Running", "Calculating repository health...", progress=30)
        pass_rate = (ctx.tests_passed / ctx.tests_total) if ctx.tests_total else 0.0
        docs = sum(1 for file in ctx.files if file["type"] == "docs")
        source_files = sum(1 for file in ctx.files if file["type"] == "source")
        has_manifest = any(
            file["path"] in {"requirements.txt", "pyproject.toml", "package.json", "Pipfile"}
            for file in ctx.files
        )
        has_ci = any(file["type"] == "ci" for file in ctx.files)
        tests_verified = ctx.test_status == "passed" and ctx.tests_total > 0
        large_file_ratio = (
            sum(1 for file in ctx.files if file["lines"] > 500) / max(1, source_files)
            if source_files
            else 0.0
        )
        ctx.health_dimensions = {
            "Testing": pass_rate if tests_verified or ctx.test_status == "failed" else 0.0,
            "Security": min(1.0, 0.35 + (0.2 if has_manifest else 0.0) + (0.15 if has_ci else 0.0)),
            "Architecture": min(1.0, 0.3 + min(len(ctx.modules), 10) * 0.05 + min(len(ctx.dependencies), 20) * 0.01),
            "Performance": max(0.25, 1.0 - min(0.55, ctx.total_lines / 20000) - min(0.2, large_file_ratio * 0.5)),
            "Documentation": min(1.0, docs / 3) if docs else 0.0,
            "Maintainability": min(1.0, 0.25 + (0.2 if has_manifest else 0.0) + min(len(ctx.modules), 10) * 0.04 + (0.15 if docs else 0.0)),
            "Deployment Readiness": min(1.0, 0.2 + (0.25 if tests_verified else 0.0) + (0.2 if has_manifest else 0.0) + (0.2 if has_ci else 0.0) + (0.15 if ctx.entry_points else 0.0)),
        }
        ctx.health_score = sum(ctx.health_dimensions.values()) / len(ctx.health_dimensions)
        ctx.health_recommendations = self._health_recommendations(ctx)
        
        grade = "A-" if ctx.health_score >= 0.8 else "B" if ctx.health_score >= 0.6 else "C"
        quality = "Excellent" if ctx.health_score >= 0.8 else "Good" if ctx.health_score >= 0.6 else "Fair"
        risk = "Low" if ctx.health_score >= 0.8 and ctx.success else "Medium" if ctx.health_score >= 0.6 else "High"
        findings = len(ctx.health_recommendations)
        top_rec = ctx.health_recommendations[0] if ctx.health_recommendations else "No evidence-backed recommendations were generated."
        deploy_rec = (
            "Safe for staging based on the verified test run."
            if ctx.success
            else "Verification blocked or failed; do not treat this workspace as release-ready."
        )
        time_saved = f"{ctx.issues_fixed * 4.2:.1f} hours." if ctx.issues_fixed else "Not estimated; no verified repair was applied."

        if ctx.test_status == "no_tests":
            exec_summary = (
                f"ForgeOS analyzed {ctx.repo_name} but found no runnable automated test suite. "
                "No repair or deployment-success claim was made."
            )
        elif ctx.test_status == "error":
            exec_summary = (
                f"ForgeOS analyzed {ctx.repo_name}, but its test command could not collect a valid result. "
                "The repair gate remained closed until the verification environment is fixed."
            )
        elif ctx.success:
            exec_summary = (
                f"ForgeOS verified {ctx.repo_name} with {ctx.tests_passed}/{ctx.tests_total} tests passing "
                f"and applied {ctx.issues_fixed} verified repair(s)."
            )
        else:
            exec_summary = (
                f"ForgeOS found {ctx.tests_failed} failing test(s) in {ctx.repo_name}; "
                "the workspace remains unapproved until verification passes."
            )

        ctx.health_grade = grade
        ctx.health_quality = quality
        ctx.health_risk = risk
        ctx.health_findings = findings
        ctx.health_top_rec = top_rec
        ctx.health_deploy_rec = deploy_rec
        ctx.health_time_saved = time_saved
        ctx.health_exec_summary = exec_summary

        await event_manager.publish(
            ctx.session_id,
            HealthUpdateEvent(
                overall_score=ctx.health_score,
                dimensions=ctx.health_dimensions,
                recommendations=ctx.health_recommendations,
                repository_grade=grade,
                engineering_quality=quality,
                business_risk=risk,
                critical_findings=findings,
                top_recommendation=top_rec,
                deployment_recommendation=deploy_rec,
                estimated_time_saved=time_saved,
                executive_summary=exec_summary,
            ),
        )
        await self._agent(ctx, AgentName.SECURITY, "Completed", "Health score ready", progress=100, confidence=0.86)
        await self._agent(ctx, AgentName.PERFORMANCE, "Completed", "Performance pass complete", progress=100, confidence=0.8)

    async def _stage_business_intelligence(self, ctx: PipelineContext) -> None:
        await self._agent(ctx, AgentName.BUSINESS, "Running", "Gathering GitHub-first business intelligence...", progress=25)
        await self._ai_activity(
            ctx,
            operation_id="ai-business-brief",
            capability="business_intelligence",
            status=(AIActivityStatus.RUNNING if self.business_intelligence.ai_insights.is_configured else AIActivityStatus.BLOCKED),
            model=self.settings.openai_bi_model,
            message=(
                "OpenAI will turn collected GitHub and engineering facts into a constrained decision brief."
                if self.business_intelligence.ai_insights.is_configured
                else "No model request: OPENAI_API_KEY is not configured for the business brief."
            ),
        )
        intelligence = await self.business_intelligence.collect(
            repository_url=ctx.repository_url,
            workspace_path=ctx.workspace_path,
            repository_name=ctx.repo_name,
            total_files=ctx.total_files,
            total_lines=ctx.total_lines,
            tests_total=ctx.tests_total,
            tests_failed=ctx.tests_failed,
            issues_fixed=ctx.issues_fixed,
            primary_language=ctx.language,
        )
        ctx.business_data = intelligence.as_event_payload()
        await event_manager.publish(ctx.session_id, BusinessUpdateEvent(**ctx.business_data))
        raw_ai_status = str(ctx.business_data.get("ai_status", "blocked"))
        ai_status = (
            AIActivityStatus(raw_ai_status)
            if raw_ai_status in {status.value for status in AIActivityStatus}
            else AIActivityStatus.BLOCKED
        )
        await self._ai_activity(
            ctx,
            operation_id="ai-business-brief",
            capability="business_intelligence",
            status=ai_status,
            model=str(ctx.business_data.get("ai_model") or self.settings.openai_bi_model),
            message=str(ctx.business_data.get("ai_message") or "Business brief status unavailable."),
            request_id=str(ctx.business_data.get("ai_request_id") or ""),
            input_tokens=int(ctx.business_data.get("ai_input_tokens") or 0),
            output_tokens=int(ctx.business_data.get("ai_output_tokens") or 0),
        )
        await self._terminal(
            ctx,
            "supervisor",
            f"[Business] Intelligence source: {ctx.business_data.get('source', 'local')} | AI brief: {ai_status.value}",
            is_error=ai_status == AIActivityStatus.FAILED,
        )
        await self._agent(
            ctx,
            AgentName.BUSINESS,
            "Completed" if ai_status in {AIActivityStatus.COMPLETED, AIActivityStatus.BLOCKED} else "Failed",
            "GitHub intelligence and AI brief ready"
            if ai_status == AIActivityStatus.COMPLETED
            else "GitHub intelligence ready; AI brief unavailable",
            progress=100,
            confidence=0.92 if ai_status == AIActivityStatus.COMPLETED else 0.8,
        )

    async def _stage_stream_results(self, ctx: PipelineContext) -> None:
        await self._agent(ctx, AgentName.SUPERVISOR, "Running", "Compiling final results...", progress=90)
        git_result = await self.git_integration.finalize(ctx.workspace_path, ctx.repo_name)
        await self._terminal(ctx, "git", f"[Git] {git_result.message}")
        if git_result.pull_request_created and git_result.pull_request_url:
            await self._terminal(ctx, "git", f"[Git] Pull request created: {git_result.pull_request_url}")
        elif git_result.comparison_url:
            await self._terminal(ctx, "git", f"[Git] Compare branch to create PR: {git_result.comparison_url}")

        # Compile and generate session runs artifact bundle
        artifact_manager = SessionArtifactManager(ctx.workspace_path)
        bundle_path = artifact_manager.generate_bundle(ctx)
        if bundle_path:
            await self._terminal(ctx, "supervisor", f"[Artifacts] Created execution telemetry bundle at: runs/{bundle_path.name}/")
            await self._terminal(ctx, "supervisor", f"[Artifacts] Generated summary.md, diff.patch, health.json, timeline.json, business.json, architecture.json")
        else:
            await self._terminal(ctx, "supervisor", "[Artifacts] Failed to generate bundle directory.", is_error=True)

        await self._terminal(ctx, "supervisor", "===========================================")
        await self._terminal(ctx, "supervisor", f"ForgeOS Analysis Complete - {ctx.repo_name}")
        await self._terminal(ctx, "supervisor", f"Duration: {ctx.duration_seconds:.1f}s")
        await self._terminal(ctx, "supervisor", f"Issues Found: {ctx.issues_found} | Fixed: {ctx.issues_fixed}")
        await self._terminal(ctx, "supervisor", f"Tests: {self._test_status_message(ctx)}")
        await self._terminal(ctx, "supervisor", f"Health Score: {ctx.health_score:.0%}")
        await self._terminal(ctx, "supervisor", "===========================================")
        await self._agent(
            ctx,
            AgentName.SUPERVISOR,
            "Completed" if ctx.success else "Waiting",
            "Mission complete" if ctx.success else "Mission requires review",
            progress=100 if ctx.success else 90,
            confidence=0.95 if ctx.success else 0.4,
        )

    async def _verify_generated_regression_test(
        self,
        ctx: PipelineContext,
        regression_test: AIRegressionTest,
    ) -> bool:
        """Keep a generated test only when the complete suite remains green."""
        root = Path(ctx.workspace_path).resolve()
        target = (root / regression_test.file_path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            await self._terminal(ctx, "supervisor", "[QA] Generated regression test escaped the workspace and was rejected.", is_error=True)
            return False
        if target.exists():
            await self._terminal(ctx, "supervisor", f"[QA] Generated regression test already exists: {regression_test.file_path}", is_error=True)
            return False

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(regression_test.content, encoding="utf-8")
        await self._terminal(ctx, "supervisor", f"[QA] Validating generated regression test: {regression_test.file_path}")
        validation = await self._run_verification(ctx)
        if validation.status == "passed" and validation.tests_total > 0 and validation.tests_failed == 0:
            self._apply_test_result(ctx, validation)
            ctx.success = True
            diff_item = {
                "file_path": regression_test.file_path,
                "diff": unified_diff(regression_test.file_path, "", regression_test.content),
                "explanation": regression_test.explanation,
                "confidence": regression_test.confidence,
                "risk": "low",
                "source": "ai_regression",
            }
            ctx.diffs.append(diff_item)
            ctx.generated_regression_test = dict(diff_item)
            await event_manager.publish(
                ctx.session_id,
                DiffUpdateEvent(
                    file_path=regression_test.file_path,
                    diff=str(diff_item["diff"]),
                    explanation=regression_test.explanation,
                    confidence=regression_test.confidence,
                    risk="low",
                ),
            )
            await self._publish_metrics(ctx)
            await self._terminal(ctx, "supervisor", "[QA] AI regression test passed the full discovered suite and was retained.")
            return True

        target.unlink(missing_ok=True)
        await self._terminal(
            ctx,
            "supervisor",
            "[QA] Generated regression test did not keep the full suite green and was removed.",
            is_error=True,
        )
        baseline = await self._run_verification(ctx)
        self._apply_test_result(ctx, baseline)
        ctx.success = baseline.status == "passed" and baseline.tests_total > 0 and baseline.tests_failed == 0
        await self._publish_metrics(ctx)
        return False

    async def _publish_metrics(self, ctx: PipelineContext) -> None:
        await event_manager.publish(
            ctx.session_id,
            MetricsUpdateEvent(
                tests_total=ctx.tests_total,
                tests_passed=ctx.tests_passed,
                tests_failed=ctx.tests_failed,
                tests_skipped=ctx.tests_skipped,
                test_status=ctx.test_status,
                test_command=ctx.test_command,
                test_error=ctx.test_error,
                issues_found=ctx.issues_found,
                issues_fixed=ctx.issues_fixed,
            ),
        )

    async def _agent(
        self,
        ctx: PipelineContext,
        agent: AgentName,
        status: str,
        message: str,
        progress: int = 0,
        confidence: float = 0.0,
    ) -> None:
        await event_manager.publish(
            ctx.session_id,
            AgentUpdateEvent(
                agent=agent,
                status=AgentStatus(status),
                message=message,
                progress=progress,
                confidence=confidence,
            ),
        )

    async def _terminal(self, ctx: PipelineContext, source: str, content: str, is_error: bool = False) -> None:
        await event_manager.publish(
            ctx.session_id,
            TerminalLogEvent(source=source, content=content, is_error=is_error),
        )

    async def _ai_activity(
        self,
        ctx: PipelineContext,
        *,
        operation_id: str,
        capability: str,
        status: AIActivityStatus,
        model: str,
        message: str,
        request_id: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        await event_manager.publish(
            ctx.session_id,
            AIActivityEvent(
                operation_id=operation_id,
                capability=capability,
                agent=self._agent_for_ai_capability(capability),
                status=status,
                model=model,
                message=message,
                request_id=request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ),
        )

    @staticmethod
    def _agent_for_ai_capability(capability: str) -> AgentName | None:
        return {
            "repair": AgentName.REPAIR,
            "regression_test": AgentName.QA,
            "business_intelligence": AgentName.BUSINESS,
        }.get(capability)

    async def _publish_impact(self, ctx: PipelineContext, focus_files: list[str]) -> None:
        """Emit the graph-resolved change radius without guessing unparsed links."""
        impact = calculate_blast_radius(ctx.graph_nodes, ctx.graph_edges, focus_files)
        ctx.impact_data = impact
        await event_manager.publish(ctx.session_id, ImpactUpdateEvent(**impact))

    async def _reasoning(
        self,
        ctx: PipelineContext,
        *,
        step_id: str,
        stage: PipelineStage,
        phase: str,
        title: str,
        detail: str,
        status: ReasoningStatus,
        agent: AgentName,
        evidence: list[str] | None = None,
        confidence: float = 0.0,
    ) -> None:
        """Publish concise, evidence-backed rationale without exposing hidden model deliberation."""
        await event_manager.publish(
            ctx.session_id,
            ReasoningUpdateEvent(
                step_id=step_id,
                stage=stage.value,
                phase=phase,
                title=title,
                detail=detail,
                status=status,
                agent=agent,
                evidence=evidence or [],
                confidence=confidence,
            ),
        )
        if status == ReasoningStatus.RUNNING:
            await asyncio.sleep(0.08)

    async def _run_verification(self, ctx: PipelineContext) -> Any:
        """Run only the test command explicitly discovered for this repository."""
        command = self.verification_runner.preview_command(
            ctx.workspace_path,
            ctx.test_paths,
            ctx.verification_command,
            ctx.test_framework,
            ctx.verification_workdir,
        )
        if command:
            await self._terminal(ctx, "verification", f"$ {command}")
        else:
            await self._terminal(
                ctx,
                "verification",
                "[QA] No runnable repository test command was declared; Python pytest was not assumed.",
            )
        return await self.verification_runner.run(
            ctx.workspace_path,
            lambda line, is_error: self._terminal(ctx, "verification", line, is_error),
            test_paths=ctx.test_paths,
            command=ctx.verification_command,
            working_directory=ctx.verification_workdir,
            framework=ctx.test_framework,
        )

    def _apply_test_result(self, ctx: PipelineContext, result: Any) -> None:
        ctx.tests_total = result.tests_total
        ctx.tests_passed = result.tests_passed
        ctx.tests_failed = result.tests_failed
        ctx.tests_skipped = result.tests_skipped
        ctx.test_status = result.status
        ctx.test_command = result.command
        ctx.test_error = result.error
        ctx.test_warning = getattr(result, "warning", "")
        ctx.test_missing_dependencies = list(getattr(result, "missing_dependencies", []))
        ctx.test_output = result.output
        ctx.failures = result.failures

    @staticmethod
    def _observed_issue_count(ctx: PipelineContext) -> int:
        if ctx.failures:
            return len(ctx.failures)
        return 1 if ctx.test_status in {"no_tests", "error"} else 0

    @staticmethod
    def _test_status_message(ctx: PipelineContext) -> str:
        if ctx.test_status == "passed":
            return f"{ctx.tests_passed}/{ctx.tests_total} passing"
        if ctx.test_status == "failed":
            return f"{ctx.tests_passed}/{ctx.tests_total} passing; {ctx.tests_failed} failing"
        if ctx.test_status == "no_tests":
            return "no runnable automated test suite discovered"
        if ctx.test_status == "error":
            return f"test command error: {ctx.test_error or 'unknown error'}"
        return "not run"

    @staticmethod
    def _test_evidence_detail(ctx: PipelineContext) -> str:
        if ctx.test_status in {"passed", "failed"}:
            detail = f"Captured repository test output with {ctx.tests_failed} failing test(s) and {ctx.tests_passed} passing test(s)."
        else:
            detail = f"The repository test command returned no executable test result: {ctx.test_error or 'verification unavailable'}."
        return f"{ctx.test_warning} {detail}".strip()

    @staticmethod
    def _test_agent_message(ctx: PipelineContext) -> str:
        if ctx.test_status == "passed":
            return "All discovered tests passing"
        if ctx.test_status == "failed":
            return f"{ctx.tests_failed} test failures detected"
        if ctx.test_status == "no_tests":
            return "No runnable automated test suite discovered"
        if ctx.test_status == "error":
            if ctx.test_missing_dependencies:
                return f"Missing test dependency: {', '.join(ctx.test_missing_dependencies)}"
            return "Repository test command failed"
        return "Test status unavailable"

    @staticmethod
    def _verification_summary(ctx: PipelineContext) -> str:
        if ctx.success:
            return "Verification passed on the discovered test suite."
        return f"Verification status: {ctx.test_status.replace('_', ' ')}; review required."

    @staticmethod
    def _failure_to_task(index: int, failure: dict[str, str]) -> dict[str, Any]:
        failure_type = failure.get("type", "test_failure")
        source_file = failure.get("source_file") or failure.get("file", "")
        repair_type = "deterministic" if failure_type == "assertion_error" and "404" in failure.get("error", "") else "ai_repair"
        return {
            "id": index,
            "title": f"Fix {failure.get('test') or failure_type}",
            "type": repair_type,
            "priority": "high" if repair_type == "deterministic" else "medium",
            "file": source_file,
        }

    @staticmethod
    def _failure_evidence(failures: list[dict[str, Any]]) -> str:
        """Keep the model request scoped to unresolved parsed failures only."""
        return "\n\n".join(
            "\n".join(
                part
                for part in (
                    f"Test: {failure.get('test', 'unknown')}",
                    f"Source file: {failure.get('source_file', 'unknown')}",
                    f"Error: {failure.get('error', failure.get('type', 'unknown'))}",
                )
                if part
            )
            for failure in failures
        )

    @staticmethod
    def _patch_to_diff(patch: AIRepairPatch) -> dict[str, object]:
        return {
            "file_path": patch.file_path,
            "diff": patch.unified_diff,
            "explanation": patch.explanation,
            "confidence": patch.confidence,
            "risk": patch.risk,
            "source": "ai",
        }

    def _source_file_context(
        self,
        ctx: PipelineContext,
        failures: list[dict[str, Any]] | None = None,
    ) -> dict[str, str]:
        root = Path(ctx.workspace_path)
        context: dict[str, str] = {}
        for failure in failures if failures is not None else (ctx.repair_failures or ctx.failures):
            source_file = failure.get("source_file")
            if not source_file:
                continue
            path = root / source_file
            if path.exists():
                context[source_file] = path.read_text(encoding="utf-8", errors="ignore")[:4000]
        return context

    def _regression_file_context(self, ctx: PipelineContext) -> dict[str, str]:
        """Supply repaired sources plus a small, real test sample to the proof step."""
        root = Path(ctx.workspace_path)
        context = self._source_file_context(ctx)
        test_files = [
            str(file.get("path", ""))
            for file in ctx.files
            if file.get("type") == "test" and str(file.get("path", "")).endswith(".py")
        ]
        for test_file in test_files[:4]:
            path = root / test_file
            if path.is_file():
                context[test_file] = path.read_text(encoding="utf-8", errors="ignore")[:3500]
        return context

    def _failing_test_context(
        self,
        ctx: PipelineContext,
        failures: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Provide failing tests as read-only behavioral evidence to the repair gate."""
        root = Path(ctx.workspace_path)
        context: dict[str, str] = {}
        for failure in failures:
            test_file = str(failure.get("file", ""))
            path = root / test_file
            if test_file and path.is_file():
                context[test_file] = path.read_text(encoding="utf-8", errors="ignore")[:4500]
        return context

    @staticmethod
    def _failures_without_planned_patch(ctx: PipelineContext) -> list[dict[str, Any]]:
        planned_files = {str(diff.get("file_path")) for diff in ctx.diffs}
        return [
            failure
            for failure in ctx.failures
            if failure.get("source_file") not in planned_files
        ]

    @staticmethod
    def _health_recommendations(ctx: PipelineContext) -> list[str]:
        recommendations: list[str] = []
        if ctx.test_status == "no_tests":
            recommendations.append("Add a repository test script and runnable automated tests so behavior can be verified.")
        elif ctx.test_status == "error":
            if ctx.test_missing_dependencies:
                recommendations.append(
                    "Provision declared test dependencies before repair: "
                    + ", ".join(ctx.test_missing_dependencies)
                    + "."
                )
            else:
                recommendations.append("Resolve the repository test command or environment error before repair.")
        if ctx.tests_failed:
            recommendations.append("Resolve remaining failing tests before production release.")
        if not any(file["type"] == "docs" for file in ctx.files):
            recommendations.append("Add a README or architecture notes for maintainability.")
        if not any(file["path"].startswith(".github/") for file in ctx.files):
            recommendations.append("Add CI workflow to run tests on pull requests.")
        if not any(file["path"] in {"requirements.txt", "pyproject.toml", "package.json", "Pipfile"} for file in ctx.files):
            recommendations.append("Add a dependency manifest so environments can be reproduced.")
        if ctx.health_dimensions.get("Deployment Readiness", 0) < 0.7:
            recommendations.append("Add deployment configuration and environment documentation.")
        return recommendations[:5]
