from fastapi import APIRouter, BackgroundTasks, Body, Request, Query, HTTPException
import asyncio
import json
from typing import Any, Optional
from sse_starlette.sse import EventSourceResponse

from app.database import get_db_connection

router = APIRouter()

# Per-client SSE subscriptions: each GET /live connection gets its own queue
# so one client never steals another client's events (global-queue fan-out bug).
_subscribers: set[asyncio.Queue] = set()


async def _broadcast(event: dict[str, Any]) -> None:
    """Fan-out event to all connected SSE clients; drop oldest on full."""
    dead: list[asyncio.Queue] = []
    for q in list(_subscribers):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        except Exception:
            dead.append(q)
    for q in dead:
        _subscribers.discard(q)


async def _fail_running_jobs(profile_id: int, error: str) -> None:
    try:
        async with get_db_connection() as conn:
            await conn.execute(
                """UPDATE scan_jobs SET status='FAILED', completed_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP WHERE search_profile_id=? AND UPPER(status)='RUNNING'""",
                (profile_id,),
            )
            await conn.commit()
    except Exception:
        pass


async def _complete_job(job_id: int, leads_found: int) -> None:
    try:
        async with get_db_connection() as conn:
            await conn.execute(
                """UPDATE scan_jobs SET status='COMPLETED', completed_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP, leads_found=?, items_found=?
                   WHERE id=?""",
                (leads_found, leads_found, job_id),
            )
            await conn.commit()
    except Exception:
        pass


async def _fail_job(job_id: int) -> None:
    try:
        async with get_db_connection() as conn:
            await conn.execute(
                """UPDATE scan_jobs SET status='FAILED', completed_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (job_id,),
            )
            await conn.commit()
    except Exception:
        pass


async def _load_profile_platforms(profile_id: int) -> list[str]:
    """Return profile's configured platforms, falling back to reddit+hackernews."""
    try:
        async with get_db_connection() as conn:
            cur = await conn.execute(
                "SELECT platforms FROM search_profiles WHERE id = ?", (profile_id,)
            )
            row = await cur.fetchone()
            if row and row["platforms"]:
                raw = row["platforms"]
                if isinstance(raw, str):
                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, list) and parsed:
                            return [str(p).lower() for p in parsed if str(p).strip()]
                    except Exception:
                        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
                        if parts:
                            return parts
                elif isinstance(raw, list) and raw:
                    return [str(p).lower() for p in raw if str(p).strip()]
    except Exception:
        pass
    return ["reddit", "hackernews"]


async def run_scan_task(
    profile_id: int,
    platforms: Optional[list[str]] = None,
    job_ids: Optional[list[int]] = None,
):
    """Run scan pipeline in background and push SSE events."""
    from app.scheduler.pipeline import build_default_pipeline

    job_map: dict[str, int] = {}
    if platforms and job_ids and len(job_ids) == len(platforms):
        job_map = {str(p).lower(): j for p, j in zip(platforms, job_ids)}

    await _broadcast({"event": "scan_started", "data": json.dumps({"profile_id": profile_id})})
    try:
        pipeline = build_default_pipeline()
        if platforms:
            for plat in platforms:
                plat_norm = str(plat).lower()
                await _broadcast({"event": "item_found", "data": json.dumps({"platform": plat_norm})})
                try:
                    res = await pipeline.run_scan(profile_id, plat_norm)
                    leads = res.get("leads_found", 0) if isinstance(res, dict) else 0
                    if plat_norm in job_map:
                        await _complete_job(job_map[plat_norm], int(leads or 0))
                    await _broadcast(
                        {"event": "lead_qualified", "data": json.dumps({"platform": plat_norm, "leads_found": leads})}
                    )
                except Exception as e:
                    if plat_norm in job_map:
                        await _fail_job(job_map[plat_norm])
                    await _broadcast({"event": "error", "data": json.dumps({"platform": plat_norm, "message": str(e)[:500]})})
        else:
            results = await pipeline.run_full_scan(profile_id)
            total = sum(r.get("leads_found", 0) for r in results if isinstance(r, dict))
            await _broadcast({"event": "lead_qualified", "data": json.dumps({"total": total})})
    except Exception as e:
        await _broadcast({"event": "error", "data": json.dumps({"message": str(e)[:500]})})
        await _fail_running_jobs(profile_id, str(e))
    await _broadcast({"event": "scan_completed", "data": json.dumps({"status": "completed"})})


async def _create_scan_jobs(pid: int, norm_platforms: list[str]) -> list[int]:
    """Insert one RUNNING scan_jobs row per platform; return ids in order."""
    job_ids: list[int] = []
    async with get_db_connection() as conn:
        for plat in norm_platforms:
            cur = await conn.execute(
                "INSERT INTO scan_jobs (search_profile_id, profile_id, platform, status) VALUES (?, ?, ?, ?)",
                (pid, pid, plat, "RUNNING"),
            )
            job_ids.append(cur.lastrowid)
        await conn.commit()
    return job_ids


@router.post("/trigger")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    search_profile_id: Optional[int] = Body(None),
    profile_id: Optional[int] = Body(None),
    persona_id: Optional[int] = Body(None),
    platforms: Optional[list[str]] = Body(None),
) -> dict[str, Any]:
    """Trigger scan for a profile. Accepts search_profile_id / profile_id / persona_id aliases."""
    pid = search_profile_id or profile_id or persona_id
    if pid is None:
        raise HTTPException(status_code=422, detail="search_profile_id (or profile_id/persona_id) is required")
    # Validate profile exists instead of silently scanning ghost id 1
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM search_profiles WHERE id = ?", (pid,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Profile {pid} not found")

    if platforms:
        norm_platforms = [str(p).lower() for p in platforms if str(p).strip()]
        if not norm_platforms:
            norm_platforms = await _load_profile_platforms(pid)
    else:
        # Respect the profile's configured platforms instead of hardcoded reddit
        norm_platforms = await _load_profile_platforms(pid)

    job_ids = await _create_scan_jobs(pid, norm_platforms)

    background_tasks.add_task(run_scan_task, pid, norm_platforms, job_ids)
    return {"scan_job_id": job_ids[0] if job_ids else None, "scan_job_ids": job_ids, "status": "started"}


@router.post("/start")
async def start_scan_alias(
    background_tasks: BackgroundTasks,
    platform: str = Body("reddit"),
    persona_id: Optional[int] = Body(None),
    search_profile_id: Optional[int] = Body(None),
    profile_id: Optional[int] = Body(None),
) -> dict[str, Any]:
    """Alias for docs-style POST /scan/start {platform, persona_id}."""
    pid = search_profile_id or profile_id or persona_id
    if pid is None:
        raise HTTPException(status_code=422, detail="search_profile_id (or profile_id/persona_id) is required")
    norm = [str(platform).lower()] if str(platform).strip() else await _load_profile_platforms(pid)
    job_ids = await _create_scan_jobs(pid, norm)
    background_tasks.add_task(run_scan_task, pid, norm, job_ids)
    return {"scan_job_id": job_ids[0] if job_ids else None, "scan_job_ids": job_ids, "status": "started"}


@router.get("/status")
async def get_scan_status() -> dict[str, Any]:
    """Get active scan status (case-insensitive, RUNNING wins)."""
    async with get_db_connection() as conn:
        cur = await conn.execute(
            "SELECT * FROM scan_jobs WHERE UPPER(status) = 'RUNNING' ORDER BY started_at DESC LIMIT 1"
        )
        row = await cur.fetchone()
        if row:
            return dict(row)
        return {"status": "idle"}


@router.get("/history")
async def get_scan_history(
    profile_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List past scan jobs."""
    async with get_db_connection() as conn:
        query = "SELECT * FROM scan_jobs WHERE 1=1"
        params: list[Any] = []

        if profile_id:
            query += " AND (search_profile_id = ? OR profile_id = ?)"
            params.extend([profile_id, profile_id])
        if status:
            query += " AND status = ?"
            params.append(status)
        if platform:
            query += " AND platform = ?"
            params.append(platform)

        cur = await conn.execute(f"SELECT COUNT(*) as cnt FROM ({query})", params)
        crow = await cur.fetchone()
        total = crow["cnt"] if crow else 0

        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])

        cur = await conn.execute(query, params)
        items = [dict(r) for r in await cur.fetchall()]

        return {"items": items, "total": total, "page": page, "per_page": per_page}


@router.get("/live")
async def live_radar(request: Request):
    """SSE endpoint for live radar (per-client subscription)."""

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        _subscribers.add(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "keepalive", "retry": 15000}
        except asyncio.CancelledError:
            pass
        finally:
            _subscribers.discard(queue)

    return EventSourceResponse(event_generator())
