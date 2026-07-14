import asyncio

import pytest

from app.events.manager import EventManager, SessionLimitExceeded
from app.models.events import TerminalLogEvent


def test_closed_session_buffer_expires_after_ttl() -> None:
    async def close_and_expire() -> tuple[int, bool]:
        manager = EventManager(session_ttl_seconds=60)
        manager.create_session("expired-session")
        await manager.publish("expired-session", TerminalLogEvent(content="completed"))
        await manager.close_session("expired-session")

        removed = manager.cleanup_expired_sessions(now=manager._closed_at["expired-session"] + 61)
        return removed, manager.has_session("expired-session")

    removed, exists = asyncio.run(close_and_expire())

    assert removed == 1
    assert not exists


def test_retention_limit_evicts_only_closed_sessions() -> None:
    async def close_sessions() -> tuple[bool, bool, bool]:
        manager = EventManager(max_retained_sessions=1)
        manager.create_session("closed-first")
        await manager.close_session("closed-first")
        manager.create_session("active")
        manager.create_session("closed-last")
        await manager.close_session("closed-last")
        return (
            manager.has_session("closed-first"),
            manager.has_session("closed-last"),
            manager.has_session("active"),
        )

    first_exists, last_exists, active_exists = asyncio.run(close_sessions())

    assert not first_exists
    assert last_exists
    assert active_exists


def test_active_session_limit_rejects_new_analysis() -> None:
    manager = EventManager(max_active_sessions=1)
    manager.create_session("first")

    with pytest.raises(SessionLimitExceeded, match="already running 1 analyses"):
        manager.create_session("second")
