# Phase 1 — Foundation & Skeleton

## Goal
Get both applications running with SSE bridge and a functional Mission Control layout.
All panels render, SSE events flow from backend to frontend, and the neo-brutalist design system is in place.

## Backend Deliverables
- FastAPI application with CORS and lifespan
- `POST /api/analyze` and `GET /api/stream` endpoints
- Pydantic models for all SSE event types
- SSE event manager with async queue per session
- Pipeline orchestrator skeleton (mock events for demo)
- Pipeline state machine

## Frontend Deliverables
- Next.js 15 App Router with TypeScript + TailwindCSS
- Neo-brutalist design system (thick borders, offset shadows, bright accents)
- SSE hook (`useEventStream`) connecting to backend
- Central state management driven by SSE (`usePipelineState`)
- All Mission Control panel components (shells with real layout)
- Repository URL input with launch button
- 8 Agent Cards with mascots, status, progress, speech bubbles
- Timeline, Live Terminal, Diff Viewer, Health Dashboard, Business Dashboard
- Repository Graph and Repository Tree panels

## Success Criteria
- `uvicorn` starts on port 8000
- `npm run dev` starts on port 3000
- Entering a URL and clicking "Launch" triggers SSE events
- All dashboard panels populate with streamed data
- UI looks polished with neo-brutalist design language
