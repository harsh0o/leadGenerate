from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.config import get_settings
from app.__init__ import __version__, __author__
import logging

from app.api.router import api_router
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LeadHunter AI...")
    await init_db()
    try:
        setup_scheduler(app)
    except Exception as e:
        logger.error(f"Scheduler failed to start, continuing without it: {e}")
    yield
    try:
        res = shutdown_scheduler()
        if hasattr(res, "__await__"):
            await res
    except Exception as e:
        logger.warning(f"Scheduler shutdown issue: {e}")
    logger.info("Shutting down LeadHunter AI...")


def _cors_origins() -> list[str]:
    defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
    try:
        extra = (get_settings().cors_origins or "")
    except Exception:
        import os
        extra = os.getenv("CORS_ORIGINS", "")
    if extra.strip():
        defaults += [o.strip() for o in extra.split(",") if o.strip()]
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for o in defaults:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


app = FastAPI(
    title='LeadHunter AI',
    description='Automated Lead Generation using AI',
    version=__version__,
    lifespan=lifespan,
)

# CORS (env-driven via CORS_ORIGINS, comma-separated)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Canonical API prefix is /api. /api/v1 kept as deprecated alias.
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1", deprecated=True)


@app.get("/")
async def root():
    return {"name": "LeadHunter AI", "version": __version__, "docs": "/docs"}


@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse
    try:
        from app.database import get_db_connection
        async with get_db_connection() as conn:
            await conn.execute("SELECT 1")
        db = "connected"
    except Exception:
        db = "disconnected"
    code = 200 if db == "connected" else 503
    return JSONResponse(
        status_code=code,
        content={"status": "ok" if db == "connected" else "degraded", "database": db, "version": __version__},
    )
