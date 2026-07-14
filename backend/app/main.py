"""
ForgeOS Backend Application

FastAPI application with CORS and two API endpoints:
  POST /api/analyze  — starts the orchestration pipeline
  GET  /api/stream   — SSE stream for real-time updates
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    logger.info("🚀 ForgeOS Backend starting...")
    yield
    logger.info("ForgeOS Backend shutting down...")


app = FastAPI(
    title="ForgeOS",
    description="Autonomous Software Engineering Operating System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    # Permit local frontend ports used by Next.js during development and
    # production-mode smoke tests, without opening CORS to external origins.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(?::\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "forgeos-backend"}
