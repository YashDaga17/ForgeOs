# Phase 2 — Backend Pipeline (Core Engine)

## Goal
Replace mock pipeline steps with real subprocess execution for the 14-step orchestration pipeline.

## Deliverables
- Repository cloning via GitPython
- Language and framework detection (Python/FastAPI/pytest)
- Dependency graph analysis
- Architecture summary generation
- Real `pytest` subprocess execution with stdout capture
- Failure classification engine
- Deterministic fix attempts (import fixes, syntax fixes)
- Patch application via unified diff
- Test re-run and verification
- Pipeline state machine with proper transitions
- Real terminal output streaming via SSE

## Success Criteria
- Clone a real repository to workspace
- Detect Python + FastAPI + pytest
- Run pytest and capture real output
- Classify test failures accurately
- Stream real subprocess output to Live Terminal
- Pipeline progresses through all 14 steps
