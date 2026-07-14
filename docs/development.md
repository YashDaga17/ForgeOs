# Development and Validation

## Local Services

Run the backend and frontend in separate terminals:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm run dev
```

The frontend reads `NEXT_PUBLIC_API_URL` at build time. Restart Next.js after changing `frontend/.env.local`.

## Validation Commands

```bash
# Backend tests
cd backend
.venv/bin/python -m pytest tests -q

# Python import/bytecode check
.venv/bin/python -m compileall -q app

# Frontend type check, lint, and production build
cd ../frontend
npx tsc --noEmit
npm run lint
npm run build
```

The test suite covers safety helpers, configuration, dependency graph behavior, git integration, local CORS, truthful test-status classification, event retention, and AI telemetry preservation.

## Manual Smoke Test

1. Start both services.
2. Submit the bundled demo or a public GitHub repository URL.
3. Confirm the repository overview, tree, graph, agent panel, terminal, and timeline update from SSE.
4. Confirm that `no_tests` or collection errors are shown as blocked verification, not success.
5. Inspect the generated run directory under `backend/app/runs/`.

## Code Conventions

- Keep backend behavior in the single orchestrator pipeline; personas are presentation states, not separate services.
- Prefer deterministic analysis and repair paths before OpenAI calls.
- Add or update matching Pydantic and TypeScript event contracts for new streamed data.
- Avoid logging credentials, raw provider prompts, or source content beyond the bounded evidence needed for a run.
- Do not change the original repository checkout; use the session workspace.
