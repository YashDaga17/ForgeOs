"""
ForgeOS Request/Response Schemas
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """POST /api/analyze request body."""
    repository_url: str = Field(
        ...,
        description="URL of the repository to analyze",
        examples=["https://github.com/user/repo"],
    )


class AnalyzeResponse(BaseModel):
    """POST /api/analyze response body."""
    session_id: str
    status: str = "started"
    message: str = "Pipeline started. Connect to /api/stream for updates."
