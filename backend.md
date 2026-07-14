# ForgeOS Backend

The ForgeOS backend is a FastAPI service that runs one observable engineering pipeline per repository session. It prepares an isolated workspace, analyzes the repository, runs a repository-owned verification command, evaluates repair gates, produces health and GitHub business intelligence, and streams every result over Server-Sent Events (SSE).

The execution path is deterministic wherever possible. OpenAI is a guarded capability, not a default substitute for repository analysis or test execution.

## Runtime

- Python 3.12+
- FastAPI and Pydantic
- GitPython for clone and git finalization
- HTTPX for GitHub API data
- OpenAI Responses API for eligible repair, regression, and business-brief work

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

## Source Map

| Location | Responsibility |
| --- | --- |
| `backend/app/main.py` | FastAPI application, CORS, lifecycle, and routes |
| `backend/app/api/` | Analyze, SSE, health, and session endpoints |
| `backend/app/pipeline/` | Sequential orchestrator, stage state, decisions, and reasoning |
| `backend/app/repository/` | GitHub URL validation and workspace preparation |
| `backend/app/analysis/` | Repository inventory, framework detection, import graph, blast radius |
| `backend/app/verification/` | pytest and repository-owned npm test discovery/execution |
| `backend/app/services/` | Repair, OpenAI, GitHub intelligence, git operations, health, and artifacts |
| `backend/app/events/` | Bounded SSE session queues, subscribers, replay, and cleanup |
| `backend/app/models/` | Pydantic REST and event contracts |
| `backend/tests/` | Backend test suite |

## Execution Model

`POST /api/analyze` creates a session and starts the pipeline in the background. The frontend connects to `GET /api/stream?session_id=<id>` and rebuilds Mission Control from typed events. Active session capacity is bounded to four, and finished sessions expire after fifteen minutes.

The backend never edits the source checkout directly. Each run operates in `backend/app/workspaces/<session>/<repository>/`, and writes a reviewable telemetry bundle under `backend/app/runs/run-<date>-<session>/`.

Read the canonical references for details:

- [Architecture](docs/architecture.md)
- [Pipeline and Repair Gates](docs/pipeline.md)
- [API and SSE Contract](docs/api.md)
- [Configuration](docs/configuration.md)
- [Operations](docs/operations.md)

## Important Safety Boundary

Verification executes repository-owned commands on the host inside a workspace, not in a container. Use trusted repositories or a disposable environment. Container isolation is the primary future hardening item.
