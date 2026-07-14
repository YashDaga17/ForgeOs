# API and SSE Contract

The API is intentionally small. The browser starts one run, then uses one SSE stream as the source of dashboard state.

Base URL: `http://localhost:8000`

## Start a Run

`POST /api/analyze`

```json
{
  "repository_url": "https://github.com/owner/repository"
}
```

Successful response:

```json
{
  "session_id": "a1b2c3d4",
  "status": "started",
  "message": "Pipeline started. Connect to /api/stream for real-time updates."
}
```

Responses:

| Status | Meaning |
| --- | --- |
| `200` | The run was scheduled. |
| `422` | Request body validation failed. |
| `429` | Four active analyses already exist; wait for one to complete. |

## Subscribe to a Run

`GET /api/stream?session_id=<session_id>`

The endpoint returns `text/event-stream`. Each message follows the SSE `data: <JSON>` format. The server replays retained events for a known completed session before closing the stream.

An unknown explicit session ID returns `404`. Omitting `session_id` waits for the next active session for up to two minutes.

```text
data: {"event":"agent_update","agent":"Oracle","status":"Running","message":"Scanning repository structure..."}
```

## Event Types

| Event | Consumer purpose |
| --- | --- |
| `pipeline_update` | Stage label, position, and status. |
| `repository_update` | Repository identity, language, framework, files, and test metadata. |
| `architecture_update` | Modules, dependency graph, and entry points. |
| `terminal_log` | Git, verification, and supervisor log output. |
| `planner_update` | Classified repair tasks. |
| `agent_update` | Persona state, progress, confidence, and message. |
| `reasoning_update` | Evidence-backed rationale lifecycle. |
| `decision_event` | Stage decision record. |
| `diff_update` | Applied or candidate patch detail. |
| `metrics_update` | Test counts and observed/fixed issue counts. |
| `impact_update` | Deterministic graph reach for a repair target. |
| `health_update` | Repository health dimensions and recommendations. |
| `business_update` | GitHub/local business signals and AI brief fields. |
| `ai_activity` | OpenAI capability, owning persona, status, safe request metadata, and token counts. |
| `completed` | Final run summary and review requirement. |
| `error` | Unrecoverable pipeline failure. |

The backend Pydantic schemas live in `backend/app/models/events.py`; frontend mirrors are in `frontend/types/events.ts`.

## CORS

Local `localhost` and `127.0.0.1` origins are allowed on any development port. The frontend API base is configured through `NEXT_PUBLIC_API_URL` and defaults to `http://localhost:8000`.
