"""
AI Governance Crisis Simulator — FastAPI application entry point.

Phase 1: Foundation
  - Root endpoint
  - Health check endpoint
  - CORS configuration
  - Lifespan event for database startup verification

Later phases will add:
  - Simulation engine endpoints
  - WebSocket live-event streaming
  - RAG / LLM agent endpoints
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.core.database import engine
from app.schemas import RootResponse, HealthResponse

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown logic.
    On startup: verify database connectivity.
    On shutdown: dispose the connection pool.
    """
    logger.info("Starting %s [%s]", settings.APP_NAME, settings.APP_ENV)

    # Verify DB connectivity — fail fast if misconfigured
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified.")
    except Exception as exc:
        # Log but do not crash — the DB may not be available in a CI/dev
        # environment where only the API layer is being tested.
        logger.warning("Database unavailable at startup: %s", exc)

    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    await engine.dispose()


# ── App factory ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-agent AI governance crisis simulation platform.",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    @app.get("/", response_model=RootResponse, tags=["meta"])
    async def root() -> RootResponse:
        """API root — confirms the service is reachable."""
        return RootResponse(message="AI Governance Crisis Simulator API")

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    async def health() -> HealthResponse:
        """
        Health check endpoint.
        Returns 200 {"status": "healthy"} when the API process is running.
        A separate /health/db endpoint (Phase 2+) will check DB connectivity.
        """
        return HealthResponse(status="healthy")

    # Phase 2: Data layer read-only endpoints
    # Phase 3: Simulation Engine endpoints
    # Phase 6: Negotiation & Voting endpoints
    # Phase 7: Deterministic Scoring Engine endpoints
    from app.api.routes import (
        countries_router,
        scenarios_router,
        simulations_router,
        negotiations_router,
        scoring_router,
    )
    app.include_router(countries_router)
    app.include_router(scenarios_router)
    app.include_router(simulations_router)
    app.include_router(negotiations_router)
    app.include_router(scoring_router)

    return app



app = create_app()
