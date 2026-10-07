from fastapi import APIRouter, Query
from typing import Any

from app.database import get_db_connection

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """Get aggregated dashboard statistics."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT COUNT(*) as cnt FROM leads")
        total_leads = (await cur.fetchone())["cnt"]

        cur = await conn.execute(
            "SELECT COALESCE(kanban_status, status, 'NEW') as st, COUNT(*) as cnt FROM leads GROUP BY st"
        )
        leads_by_status = {r["st"]: r["cnt"] for r in await cur.fetchall()}

        cur = await conn.execute("SELECT platform, COUNT(*) as cnt FROM leads GROUP BY platform")
        leads_by_platform = {(r["platform"] or "unknown"): r["cnt"] for r in await cur.fetchall()}

        cur = await conn.execute("SELECT COUNT(*) as cnt FROM scan_jobs")
        total_scans = (await cur.fetchone())["cnt"]

        cur = await conn.execute(
            "SELECT COUNT(*) as cnt FROM scan_jobs WHERE DATE(started_at) = DATE('now')"
        )
        scans_today = (await cur.fetchone())["cnt"]

        cur = await conn.execute(
            "SELECT COUNT(*) as cnt FROM leads WHERE DATE(created_at) = DATE('now')"
        )
        leads_today = (await cur.fetchone())["cnt"]

        cur = await conn.execute("SELECT AVG(COALESCE(match_score, match_confidence, 0)) as avg_conf FROM leads")
        row = await cur.fetchone()
        avg_match_confidence = row["avg_conf"] if row and row["avg_conf"] is not None else 0.0

        cur = await conn.execute("SELECT COUNT(*) as cnt FROM search_profiles WHERE is_active = 1")
        active_profiles = (await cur.fetchone())["cnt"]

        cur = await conn.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT 5")
        recent_rows = [dict(r) for r in await cur.fetchall()]
        # Normalize recent leads for frontend (tags list, 0-100 confidence, status fallback)
        import json as _json
        recent_leads = []
        for _d in recent_rows:
            _t = _d.get("tags", "[]")
            if isinstance(_t, str):
                try:
                    _d["tags"] = _json.loads(_t) if _t else []
                except Exception:
                    _d["tags"] = []
            if _d.get("tags") is None:
                _d["tags"] = []
            _d.setdefault("kanban_status", _d.get("status", "NEW"))
            _d.setdefault("status", _d.get("kanban_status", "NEW"))
            try:
                _raw = float(_d.get("match_score", 0) or _d.get("match_confidence", 0) or 0)
            except (TypeError, ValueError):
                _raw = 0.0
            _d["match_score"] = _raw if _raw <= 1 else round(_raw / 100, 4)
            _d["match_confidence"] = _d["match_score"]
            try:
                _cs = float(_d.get("confidence_score", 0) or _raw)
            except (TypeError, ValueError):
                _cs = _raw
            _d["confidence_score"] = round(_cs * 100, 1) if 0 <= _cs <= 1 else round(_cs, 1)
            recent_leads.append(_d)

        cur = await conn.execute("SELECT COUNT(*) as cnt FROM scan_jobs WHERE UPPER(status) = 'RUNNING'")
        active_scans_row = await cur.fetchone()
        active_scans = active_scans_row["cnt"] if active_scans_row else 0

        try:
            _avg = float(avg_match_confidence or 0)
        except (TypeError, ValueError):
            _avg = 0.0
        # match_score stored 0-1; normalize to 0-100 for display
        match_accuracy = round(_avg * 100, 1) if 0 <= _avg <= 1 else round(_avg, 1)

        # Frontend-friendly aliases
        return {
            "total_leads": total_leads,
            "leads_by_status": leads_by_status,
            "leads_by_platform": leads_by_platform,
            "total_scans": total_scans,
            "scans_today": scans_today,
            "leads_today": leads_today,
            "avg_match_confidence": _avg if _avg <= 1 else round(_avg / 100, 4),
            "active_profiles": active_profiles,
            "active_scans": active_scans,
            "match_accuracy": match_accuracy,
            "recent_leads": recent_leads,
        }


@router.get("/recent-leads")
async def get_recent_leads(limit: int = Query(10, ge=1, le=50)) -> list[dict[str, Any]]:
    """Latest qualified leads."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d.setdefault("kanban_status", d.get("status", "NEW"))
            out.append(d)
        return out


@router.get("/recent-scans")
async def get_recent_scans(limit: int = Query(10, ge=1, le=50)) -> list[dict[str, Any]]:
    """Latest scan jobs with stats."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM scan_jobs ORDER BY started_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]
