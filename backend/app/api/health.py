from fastapi import APIRouter, HTTPException, Response
import time
from typing import Any

from app.database import get_db_connection
from app.models.platform_health import HealthStatus
from app.channels import get_channel
from app.config import get_settings
from app.utils.rate_limiter import get_shared_limiter

router = APIRouter()
START_TIME = time.time()


@router.get("/")
async def health_check(response: Response) -> dict[str, Any]:
    """Overall system health with version and uptime (503 when DB down)."""
    uptime = time.time() - START_TIME
    try:
        async with get_db_connection() as conn:
            await conn.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    if db_status != "connected":
        response.status_code = 503
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0",
        "uptime_seconds": uptime,
    }


@router.get("/platforms")
async def get_platform_health() -> list[dict[str, Any]]:
    """List all platform health statuses."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM platform_health")
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


@router.post("/platforms/{platform}/check")
async def check_platform_health(platform: str) -> dict[str, Any]:
    """Trigger manual health check for a specific platform (upserts row)."""
    try:
        settings = get_settings()
        channel_cls = get_channel(platform)
        channel = channel_cls(settings, get_shared_limiter())
        result = await channel.health_check()
        # health_check returns Tuple[HealthStatus, Optional[str]]
        if isinstance(result, tuple):
            status_obj, detail = result
            status = status_obj.value if hasattr(status_obj, "value") else str(status_obj)
        elif isinstance(result, bool):
            status = "HEALTHY" if result else "DOWN"
            detail = None
        else:
            status = str(result)
            detail = None

        norm = platform.lower()
        async with get_db_connection() as conn:
            cur = await conn.execute(
                "UPDATE platform_health SET status = ?, last_check_at = CURRENT_TIMESTAMP, last_check = CURRENT_TIMESTAMP, error_detail = ?, consecutive_failures = CASE WHEN ? = 'HEALTHY' THEN 0 ELSE COALESCE(consecutive_failures,0)+1 END WHERE platform = ?",
                (status, detail, status, norm),
            )
            if cur.rowcount == 0:
                await conn.execute(
                    "INSERT INTO platform_health (platform, status, last_check_at, last_check, error_detail, consecutive_failures) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)",
                    (norm, status, detail, 0 if status == "HEALTHY" else 1),
                )
            await conn.commit()

        return {"platform": norm, "status": status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
