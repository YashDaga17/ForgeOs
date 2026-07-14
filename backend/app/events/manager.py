"""
ForgeOS SSE Event Manager

Manages Server-Sent Event streams. Each analysis session gets its own
async queue. The frontend connects once via GET /api/stream and receives
all events for the active session.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from typing import AsyncGenerator

from app.models.events import BaseEvent

logger = logging.getLogger(__name__)

DEFAULT_SESSION_TTL_SECONDS = 15 * 60
DEFAULT_MAX_RETAINED_SESSIONS = 32
DEFAULT_MAX_ACTIVE_SESSIONS = 4


class SessionLimitExceeded(RuntimeError):
    """Raised when ForgeOS is already running its allowed concurrent analyses."""


class EventManager:
    """
    Central event bus for SSE streaming.

    - publish() enqueues an event for all connected clients of a session.
    - subscribe() returns an async generator that yields SSE-formatted strings.
    """

    def __init__(
        self,
        *,
        session_ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS,
        max_retained_sessions: int = DEFAULT_MAX_RETAINED_SESSIONS,
        max_active_sessions: int = DEFAULT_MAX_ACTIVE_SESSIONS,
    ) -> None:
        if session_ttl_seconds < 0:
            raise ValueError("session_ttl_seconds must be non-negative")
        if max_retained_sessions < 1:
            raise ValueError("max_retained_sessions must be at least 1")
        if max_active_sessions < 1:
            raise ValueError("max_active_sessions must be at least 1")

        self._session_ttl_seconds = session_ttl_seconds
        self._max_retained_sessions = max_retained_sessions
        self._max_active_sessions = max_active_sessions
        self._queues: dict[str, list[asyncio.Queue[BaseEvent | None]]] = defaultdict(list)
        self._active_sessions: set[str] = set()
        self._active_started_at: dict[str, float] = {}
        self._closed_sessions: set[str] = set()
        self._closed_at: dict[str, float] = {}
        self._buffers: dict[str, deque[BaseEvent]] = defaultdict(lambda: deque(maxlen=200))

    def create_session(self, session_id: str) -> None:
        """Register a new pipeline session."""
        self.cleanup_expired_sessions()
        if session_id not in self._active_sessions and len(self._active_sessions) >= self._max_active_sessions:
            raise SessionLimitExceeded(
                f"ForgeOS is already running {self._max_active_sessions} analyses. Please wait for one to finish."
            )

        self._active_sessions.add(session_id)
        self._active_started_at[session_id] = time.monotonic()
        self._closed_sessions.discard(session_id)
        self._closed_at.pop(session_id, None)
        logger.info("Session created: %s", session_id)

    async def publish(self, session_id: str, event: BaseEvent) -> None:
        """Publish an event to all subscribers of a session."""
        if session_id not in self._active_sessions:
            logger.warning("Ignoring event for inactive session: %s", session_id)
            return

        event.session_id = session_id
        self._buffers[session_id].append(event)
        queues = self._queues.get(session_id, [])
        for queue in queues:
            await queue.put(event)
        logger.debug(
            "Published %s to %d subscribers (session=%s)",
            event.event.value,
            len(queues),
            session_id,
        )

    async def subscribe(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        Subscribe to a session's event stream.
        Yields SSE-formatted strings: "data: {...}\n\n"
        """
        if not self.has_session(session_id):
            logger.warning("Subscription requested for unknown session: %s", session_id)
            return

        queue: asyncio.Queue[BaseEvent | None] = asyncio.Queue()
        self._queues[session_id].append(queue)
        logger.info("Client subscribed to session: %s", session_id)

        try:
            for buffered_event in self._buffers.get(session_id, []):
                yield self._format_sse(buffered_event)
            if session_id in self._closed_sessions:
                return
            while True:
                event = await queue.get()
                if event is None:
                    # Sentinel: stream is done
                    break
                yield self._format_sse(event)
        finally:
            queues = self._queues.get(session_id)
            if queues and queue in queues:
                queues.remove(queue)
            if not queues:
                self._queues.pop(session_id, None)
            logger.info("Client unsubscribed from session: %s", session_id)

    async def close_session(self, session_id: str) -> None:
        """Signal all subscribers that the session is complete."""
        queues = self._queues.get(session_id, [])
        for queue in queues:
            await queue.put(None)
        self._active_sessions.discard(session_id)
        self._active_started_at.pop(session_id, None)
        self._closed_sessions.add(session_id)
        self._closed_at[session_id] = time.monotonic()
        self._enforce_retained_session_limit()
        logger.info("Session closed: %s", session_id)

    def has_session(self, session_id: str) -> bool:
        """Return whether a session is active or has buffered events."""
        return session_id in self._active_sessions or session_id in self._closed_sessions

    def get_active_session(self) -> str | None:
        """Return the most recently created active session."""
        if self._active_sessions:
            return max(self._active_sessions, key=lambda session_id: self._active_started_at[session_id])
        return None

    def cleanup_expired_sessions(self, *, now: float | None = None) -> int:
        """Discard closed session buffers after their replay window has elapsed."""
        current_time = time.monotonic() if now is None else now
        expired_session_ids = [
            session_id
            for session_id, closed_at in self._closed_at.items()
            if current_time - closed_at >= self._session_ttl_seconds
        ]
        for session_id in expired_session_ids:
            self._discard_closed_session(session_id)
        if expired_session_ids:
            logger.info("Expired %d closed event session(s)", len(expired_session_ids))
        return len(expired_session_ids)

    def _enforce_retained_session_limit(self) -> None:
        overflow = len(self._closed_sessions) - self._max_retained_sessions
        if overflow <= 0:
            return

        oldest_session_ids = sorted(
            self._closed_sessions,
            key=lambda session_id: self._closed_at.get(session_id, 0.0),
        )[:overflow]
        for session_id in oldest_session_ids:
            self._discard_closed_session(session_id)
        logger.info("Evicted %d closed event session(s) to enforce retention limit", len(oldest_session_ids))

    def _discard_closed_session(self, session_id: str) -> None:
        self._closed_sessions.discard(session_id)
        self._closed_at.pop(session_id, None)
        self._buffers.pop(session_id, None)
        queues = self._queues.pop(session_id, [])
        for queue in queues:
            queue.put_nowait(None)

    @staticmethod
    def _format_sse(event: BaseEvent) -> str:
        """Format a Pydantic event as an SSE data line."""
        data = event.model_dump(mode="json")
        return f"data: {json.dumps(data)}\n\n"


# Singleton instance — shared across the application
event_manager = EventManager()
