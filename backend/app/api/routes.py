"""
ForgeOS API Routes

Two endpoints as specified:
  POST /api/analyze  — starts the orchestration pipeline
  GET  /api/stream   — SSE stream for real-time updates
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.events.manager import SessionLimitExceeded, event_manager
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.pipeline.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Single orchestrator instance
_orchestrator = Orchestrator()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Start the ForgeOS analysis pipeline for a repository.
    Returns immediately with a session_id. Connect to /api/stream for updates.
    """
    logger.info("Starting analysis for: %s", request.repository_url)

    try:
        session_id = await _orchestrator.run(request.repository_url)
    except SessionLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return AnalyzeResponse(
        session_id=session_id,
        status="started",
        message="Pipeline started. Connect to /api/stream for real-time updates.",
    )


@router.get("/stream")
async def stream_events(
    request: Request,
    session_id: str | None = Query(default=None),
) -> StreamingResponse:
    """
    Server-Sent Events stream. Streams all events for the active session.
    The frontend derives its entire UI state from this single stream.
    """
    selected_session_id = session_id or event_manager.get_active_session()

    if selected_session_id is None:
        # No active session — return an empty stream that waits
        async def wait_for_session():
            import asyncio
            # Poll until a session starts (max 120s)
            for _ in range(240):
                session_id = event_manager.get_active_session()
                if session_id:
                    async for event in event_manager.subscribe(session_id):
                        if await request.is_disconnected():
                            break
                        yield event
                    return
                await asyncio.sleep(0.5)

        return StreamingResponse(
            wait_for_session(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    if session_id is not None and not event_manager.has_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        async for event in event_manager.subscribe(selected_session_id):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
