# ForgeOS --- Product Specification v2 (Hackathon Optimized)

## Executive Summary

ForgeOS is an Autonomous Software Engineering Operating System focused
on a reliable, polished hackathon demo. The product autonomously
analyzes a repository, executes an engineering pipeline, repairs issues
using a modern OpenAI coding model, verifies results, and presents every
step through a Mission Control dashboard.

**Core principle:** The product is the orchestration and observability
layer---not the LLM.

------------------------------------------------------------------------

# Guiding Principles

-   Reliability over feature count.
-   One flawless demo is better than many unfinished features.
-   Every backend action must be visible in the UI.
-   Deterministic engineering first; AI only when required.
-   Build for Python + FastAPI + pytest in the MVP.

------------------------------------------------------------------------

# MVP Scope

Supported Repository: - Python - FastAPI - pytest

Demo repository is pre-prepared with known issues.

Target execution time: - Repository URL → Final dashboard: **under 60
seconds**.

------------------------------------------------------------------------

# High-Level Architecture

User → Next.js Mission Control → FastAPI Orchestrator → Repository
Analysis → Test Runner → Decision Engine → AI Repair Engine →
Verification → Business Intelligence → SSE Event Stream

------------------------------------------------------------------------

# AI Strategy

Use the latest OpenAI coding-capable model (for example GPT-5.x or the
current recommended coding model available through the Responses API).

Do NOT rely on legacy Codex models.

Use Structured Outputs with strict Pydantic schemas.

Expected AI response:

-   file_path
-   explanation
-   unified_diff
-   confidence
-   risk

Never request conversational markdown.

------------------------------------------------------------------------

# Backend Pipeline

1.  Clone repository.
2.  Analyze repository.
3.  Detect framework and tests.
4.  Run pytest.
5.  Classify failure.
6.  Try deterministic fixes.
7.  If unresolved, call AI.
8.  Apply patch.
9.  Re-run tests.
10. Run one targeted mutation check.
11. Generate one regression test if needed.
12. Calculate Repository Health.
13. Publish Business Intelligence.
14. Stream results to frontend.

------------------------------------------------------------------------

# Backend Folder Structure

backend/ - app/ - api/ - analysis/ - repository/ - pipeline/ -
verification/ - services/ - models/ - events/ - utils/ - workspaces/ -
demo_repository/

Repository responsibilities:

analysis/ - language detection - framework detection - dependency
graph - architecture summary

pipeline/ - orchestration - state machine - deterministic decisions

repository/ - clone - workspace - file operations

verification/ - pytest - validation

services/ - AI client - Git - filesystem - metrics

------------------------------------------------------------------------

# Frontend Folder Structure

frontend/ - app/ - components/ - MissionControl/ - RepositoryInput/ -
AgentCards/ - Timeline/ - LiveTerminal/ - DiffViewer/ -
RepositoryGraph/ - RepositoryTree/ - HealthDashboard/ -
BusinessDashboard/ - hooks/ - services/ - lib/ - types/ - styles/

------------------------------------------------------------------------

# API Design

Keep the API intentionally small.

POST /api/analyze

Input: - repository_url

Starts the orchestration pipeline.

GET /api/stream

Single Server-Sent Events stream.

Event examples: - repository_update - architecture_update -
terminal_log - planner_update - agent_update - diff_update -
metrics_update - completed

The frontend derives all UI state from this single event stream.

------------------------------------------------------------------------

# Event Payload Example

{ "event":"agent_update", "agent":"Repair", "status":"Running",
"message":"Applying patch to auth.py" }

------------------------------------------------------------------------

# UI

Design language: - Bold editorial - Thick black borders - Offset
shadows - Bright accent colors - White cards - Smooth micro animations

Mission Control panels: - Repository Overview - Repository Graph -
Repository Tree - Agent Panel - Timeline - Live Terminal - Diff Viewer -
Repository Health - Business Intelligence

------------------------------------------------------------------------

# Agent Personas (UI Only)

The UI presents specialist agents, while the backend uses a single
orchestration pipeline.

-   Supervisor
-   Repository Analyst
-   Planner
-   Repair
-   QA
-   Security
-   Performance
-   Business

Each card includes: - mascot - status - progress - confidence - speech
bubble

------------------------------------------------------------------------

# Live Terminal

Hybrid approach:

Display: - real subprocess stdout (pytest/git) - summarized supervisor
messages

This gives authenticity while remaining easy to follow during a demo.

------------------------------------------------------------------------

# Repository Health

Weighted dimensions: - Testing - Security - Architecture - Performance -
Documentation - Maintainability - Deployment Readiness

Produce: - Overall score - Category scores - Recommendations

------------------------------------------------------------------------

# Business Intelligence

Sources: - GitHub API - package ecosystem metadata - optional enrichment
via Apify (non-critical)

Show: - Stars - Forks - Contributors - Release cadence - Dependency
health - Community activity - Competitor snapshot - Executive summary

------------------------------------------------------------------------

# Demo Environment

Use a bundled demo repository and preconfigured Python environment.

Do NOT install dependencies dynamically during the live demo.

Avoid executing arbitrary repositories during judging.

------------------------------------------------------------------------

# Success Criteria

Within 30 seconds a judge should understand:

1.  ForgeOS understands repositories.
2.  ForgeOS plans engineering work.
3.  ForgeOS repairs issues with AI when necessary.
4.  Every engineering action is observable.
5.  Repository and business insights are produced automatically.
6.  The experience feels like an autonomous engineering mission control,
    not an AI chat interface.
