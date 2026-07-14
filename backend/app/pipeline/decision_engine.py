"""
ForgeOS Decision Engine

Generates structured engineering reasoning for each stage of the pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.events import DecisionEvent, AgentName
from app.pipeline.state import PipelineContext, PipelineStage


class DecisionEngine:
    """Dynamically generates decision logs for each pipeline stage."""

    @staticmethod
    def generate_decision(
        ctx: PipelineContext, stage: PipelineStage, status: str = "Completed"
    ) -> DecisionEvent:
        """Analyze the current PipelineContext and build a structured DecisionEvent."""
        
        # Default fallback values
        agent = AgentName.SUPERVISOR
        reason = "Pipeline execution stage."
        evidence = f"Stage: {stage.value}"
        action_taken = f"Executing {stage.value} handler."
        expected_outcome = "Proceed to the next pipeline stage."
        confidence = 0.95

        # Stage-specific reasoning generation
        if stage == PipelineStage.CLONE_REPOSITORY:
            agent = AgentName.SUPERVISOR
            reason = "Initialize repository analysis for user-requested repository."
            evidence = f"Target URL: {ctx.repository_url or 'demo_repository'}"
            action_taken = f"Cloned repository and prepared local workspace sandbox at {ctx.workspace_path}."
            expected_outcome = "Repository is fully cloned and available locally for static analysis."
            confidence = 1.0

        elif stage == PipelineStage.ANALYZE_REPOSITORY:
            agent = AgentName.REPOSITORY_ANALYST
            reason = "Parse codebase files and directories to build static file index."
            evidence = f"Found {ctx.total_files} files with {ctx.total_lines} total lines in workspace."
            action_taken = "Scanned repository and compiled file index with size & path listings."
            expected_outcome = "A complete repository structure mapping for framework detection."
            confidence = 0.98

        elif stage == PipelineStage.DETECT_FRAMEWORK:
            agent = AgentName.REPOSITORY_ANALYST
            reason = "Identify codebase language, framework and test targets before configuring verification."
            evidence = f"Language detected: {ctx.language or 'unknown'} | Web framework: {ctx.framework or 'unknown'} | Test runner: {ctx.test_framework or 'none'} | Targets: {len(ctx.test_paths)}"
            action_taken = f"Mapped {len(ctx.test_paths)} discovered test target(s) and the repository-declared verification command for the {ctx.framework or 'detected'} application."
            expected_outcome = "A repository-specific verification command is configured, or the run is explicitly blocked when no tests exist."
            confidence = 0.95

        elif stage == PipelineStage.RUN_TESTS:
            agent = AgentName.QA
            reason = "Execute the codebase test suite to discover existing test failures."
            environment_note = (
                f" Missing dependencies: {', '.join(ctx.test_missing_dependencies)}."
                if ctx.test_missing_dependencies
                else ""
            )
            evidence = (
                f"Status: {ctx.test_status}. Ran {ctx.tests_total} tests. Passed: {ctx.tests_passed}, "
                f"Failed: {ctx.tests_failed}, Skipped: {ctx.tests_skipped}.{environment_note}"
            )
            action_taken = f"Invoked {ctx.test_command or 'the discovered test command'} in a subprocess and captured output."
            expected_outcome = "A complete mapping of test status and traceback logs, including an explicit no-tests or collection-error result."
            confidence = 0.98

        elif stage == PipelineStage.CLASSIFY_FAILURES:
            agent = AgentName.PLANNER
            reason = "Map test errors to logical failures to design target patch fixes."
            evidence = f"Found {ctx.tests_failed} failed tests. Extracted {len(ctx.failures)} distinct failures."
            action_taken = "Grouped failures by file and error type; prepared task plan."
            expected_outcome = "A prioritized queue of files that require modification."
            confidence = 0.92

        elif stage == PipelineStage.DETERMINISTIC_FIX:
            agent = AgentName.REPAIR
            reason = "Check if test failures match known rules or pre-defined repair templates."
            evidence = f"Identified {len(ctx.failures)} failures. Planned patches: {len(ctx.diffs)}."
            action_taken = "Generated deterministic regex/template patch replacements."
            expected_outcome = "Resolve standard issues without requesting LLM resources."
            confidence = 0.90

        elif stage == PipelineStage.AI_REPAIR:
            agent = AgentName.REPAIR
            reason = "Resolve complex or custom code errors using LLM with context structure."
            ai_patches_count = len([d for d in ctx.diffs if d.get('source') == 'ai'])
            evidence = f"Found {len(ctx.failures) - len([d for d in ctx.diffs if d.get('source') == 'deterministic'])} unresolved failures requiring AI patching. Generated {ai_patches_count} AI patches."
            action_taken = "Triggered OpenAI structured repair patch generation based on source and traceback files."
            expected_outcome = "Unified patch diff generated with code fix explanation."
            confidence = 0.94 if ai_patches_count > 0 else 0.85

        elif stage == PipelineStage.APPLY_PATCH:
            agent = AgentName.REPAIR
            reason = "Merge proposed code patches back into workspace files."
            evidence = f"Found {len(ctx.diffs)} generated patch diffs to apply."
            action_taken = "Applied diffs using Git/file patch engine; updated codebase workspace."
            expected_outcome = f"Successfully integrated {ctx.issues_fixed} code patches."
            confidence = 0.96

        elif stage == PipelineStage.RERUN_TESTS:
            agent = AgentName.QA
            reason = "Validate that the applied code patches resolved the failures."
            evidence = f"Verification status: {ctx.test_status}. Total: {ctx.tests_total}, Passed: {ctx.tests_passed}, Failed: {ctx.tests_failed}."
            action_taken = "Executed the repository-specific verification command after patching."
            expected_outcome = "Only a non-empty passing test run can approve a patch."
            confidence = 0.99 if ctx.success else 0.60

        elif stage == PipelineStage.MUTATION_CHECK:
            agent = AgentName.QA
            reason = "Verify test suite resistance against trivial code regressions."
            patched_files = ", ".join(set(d.get("file_path", "") for d in ctx.diffs)) or "none"
            evidence = f"Mutation execution status: not executed. Patched files: {patched_files}."
            action_taken = "Recorded the mutation-check boundary without claiming an unexecuted test."
            expected_outcome = "A future mutation runner must execute and report targeted mutants before this stage can pass."
            confidence = 0.99

        elif stage == PipelineStage.REGRESSION_TEST:
            agent = AgentName.QA
            reason = "Produce custom test case ensuring the resolved issue does not recur."
            evidence = f"Verification status: {ctx.test_status}; existing tests: {ctx.tests_total}."
            action_taken = "Evaluated the existing test suite for regression coverage without generating a synthetic test."
            expected_outcome = "Regression coverage is approved only after a verified passing test run."
            confidence = 0.88

        elif stage == PipelineStage.CALCULATE_HEALTH:
            agent = AgentName.SECURITY
            reason = "Calculate health score and generate improvement recommendations."
            evidence = f"Calculated health score of {ctx.health_score:.0%}. Generated {len(ctx.health_recommendations)} recommendations."
            action_taken = "Aggregated results for security, tests, documentation, and maintainability."
            expected_outcome = "Repository health scorecard fully populated."
            confidence = 0.95

        elif stage == PipelineStage.BUSINESS_INTELLIGENCE:
            agent = AgentName.BUSINESS
            reason = "Correlate code quality with package registry and community stats."
            evidence = f"Community stats: Stars: {ctx.business_data.get('stars', 0)} | Forks: {ctx.business_data.get('forks', 0)} | Contributors: {ctx.business_data.get('contributors', 0)}."
            action_taken = "Collected GitHub repository metadata and package ecosystem statistics."
            expected_outcome = "Business metrics and competitor benchmarks aggregated."
            confidence = 0.90

        elif stage == PipelineStage.STREAM_RESULTS:
            agent = AgentName.SUPERVISOR
            reason = "Conclude pipeline execution and finalize repository session."
            outcome = "verified" if ctx.success else "requires review"
            evidence = f"Session {ctx.session_id} finished in {ctx.duration_seconds:.1f}s with outcome: {outcome}."
            action_taken = "Prepared final response payload, review status, and completion signals."
            expected_outcome = "All SSE stream queues resolve while the dashboard preserves the verified or review-required outcome."
            confidence = 1.0 if ctx.success else 0.9

        return DecisionEvent(
            stage=stage.value,
            agent=agent,
            reason=reason,
            evidence=evidence,
            action_taken=action_taken,
            expected_outcome=expected_outcome,
            confidence=confidence,
            status=status,
            session_id=ctx.session_id,
        )
