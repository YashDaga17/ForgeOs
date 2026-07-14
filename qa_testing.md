# ForgeOS Quality Assurance & Bug Fix Sprint — Implementation Plan

Comprehensive audit results and proposed fixes to make ForgeOS production-ready.

---

## Audit Results Summary

| Category | Issues Found |
|---|---|
| **Security** | 1 critical |
| **Deprecation Warnings** | 5 (all `datetime.utcnow()`) |
| **Type Safety** | 1 (dynamic attribute injection on dataclass) |
| **Memory / Resource** | 2 (unbounded buffers, no session cleanup) |
| **Error Handling** | 1 (missing `session_id` validation on SSE) |
| **Dead Code** | 1 (Mascot component unused) |
| **Build Warnings** | 1 (Turbopack workspace root) |
| **API Contract** | 1 (AI Insights `responses.create` API) |

> [!IMPORTANT]
> All 25 backend tests pass. The frontend builds successfully. The architecture is sound. These are targeted production-hardening fixes, not structural changes.

---

## User Review Required

> [!CAUTION]
> **CRITICAL: Real API keys are stored in `.env`**
> The file [.env](file:///Users/yashdaga/Desktop/dev/ForgeOs/.env) contains a real `OPENAI_API_KEY` and `GITHUB_TOKEN`. While `.env` is in `.gitignore`, these keys should be **rotated immediately** as a security best practice. The fix below replaces them with placeholder values and adds a warning comment.

> [!WARNING]
> **OpenAI API: `responses.create` vs `chat.completions.create`**
> The [ai_insights.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/services/ai_insights.py#L61) file uses `client.responses.create()` with an `input` parameter and `text.format` structured output. The [ai_repair.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/services/ai_repair.py) uses the same pattern. This is the **OpenAI Responses API** (newer API surface). If your `openai` SDK version doesn't support it, these calls will fail at runtime. The installed version `openai>=1.50.0` should support it — **no change needed** unless you encounter runtime errors.

---

## Proposed Changes

### Security

#### [MODIFY] [.env](file:///Users/yashdaga/Desktop/dev/ForgeOs/.env)
- **Replace real API keys with placeholder values** to prevent accidental secret exposure
- Add warning comment directing users to set real values

---

### Backend — Deprecation Fixes (`datetime.utcnow()` → `datetime.now(timezone.utc)`)

Python 3.12+ deprecates `datetime.utcnow()`. The test output shows 5 deprecation warnings tracing to three files. Fix all three.

#### [MODIFY] [state.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/pipeline/state.py)
- Line 10: Add `from datetime import timezone` import
- Line 45: Change `default_factory=datetime.utcnow` → `default_factory=lambda: datetime.now(timezone.utc)`
- Line 105: Change `datetime.utcnow()` → `datetime.now(timezone.utc)`

#### [MODIFY] [events.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/models/events.py)
- Line 10: Add `timezone` to `from datetime import datetime` import
- Line 89: Change `default_factory=datetime.utcnow` → `default_factory=lambda: datetime.now(timezone.utc)`

#### [MODIFY] [artifact_manager.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/services/artifact_manager.py)
- Line 7: Add `timezone` to `from datetime import datetime` import
- Line 24: Change `datetime.utcnow()` → `datetime.now(timezone.utc)`
- Line 63: Change `datetime.utcnow()` → `datetime.now(timezone.utc)`

---

### Backend — Type Safety (Dynamic Attribute Injection)

#### [MODIFY] [state.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/pipeline/state.py)
- Add the 8 dynamic attributes (`health_grade`, `health_quality`, `health_risk`, `health_findings`, `health_top_rec`, `health_deploy_rec`, `health_time_saved`, `health_exec_summary`) as proper typed fields on `PipelineContext` instead of using `# type: ignore` dynamic injection in [orchestrator.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/pipeline/orchestrator.py#L1061-L1068)
- Remove the `# type: ignore` comments from orchestrator.py (lines 1061-1068)
- Also add `patch_manager` as `Any | None = None` to avoid the `# type: ignore` on line 726

---

### Backend — Memory & Resource Management

#### [MODIFY] [manager.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/events/manager.py)
- **Session cleanup**: Closed sessions accumulate in `_buffers` and `_closed_sessions` forever. Add a cleanup method that removes stale sessions (called after a TTL or on new session creation when count exceeds threshold).
- **Session limit**: Add a maximum active session count guard to prevent unbounded memory growth during a demo.

#### [MODIFY] [routes.py](file:///Users/yashdaga/Desktop/dev/ForgeOs/backend/app/api/routes.py)
- **Validate `session_id` parameter**: The `/api/stream` endpoint currently accepts any string. Add a check that the session exists in `event_manager` before subscribing, returning a 404 if not found.

---

### Frontend — Dead Code Removal

#### Note: [Mascot.tsx](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/components/Mascot/Mascot.tsx)
- The `Mascot` component (311 lines) is **defined but never imported or used** by any other component. It should be kept for potential future use (it's a well-built SVG animation system). No action needed — just documenting this finding.

---

### Frontend — Build Warning Fix

#### [MODIFY] [next.config.ts](file:///Users/yashdaga/Desktop/dev/ForgeOs/frontend/next.config.ts)
- Add `turbopack.root` configuration to silence the workspace root inference warning during builds.

---

## Open Questions

1. **API Key rotation**: Have the exposed `OPENAI_API_KEY` and `GITHUB_TOKEN` in `.env` been used in production? They should be rotated regardless of whether `.env` was committed to git.

2. **OpenAI SDK version**: The code uses the newer `responses.create` API. Can you confirm the installed version works with this API surface, or should I add a `try/except` fallback to `chat.completions.create`?

---

## Verification Plan

### Automated Tests
```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -v
```
- All 25 tests must continue to pass
- The 5 `datetime.utcnow()` deprecation warnings must be eliminated

### Build Verification
```bash
cd frontend && npx next build
```
- Frontend must build with zero errors
- Turbopack workspace root warning should be resolved

### Runtime Verification
```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('OK')"
```
- All imports must resolve cleanly
