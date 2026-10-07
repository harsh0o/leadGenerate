from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.responses import StreamingResponse
import csv
import io
import json
from typing import Any, Optional

from app.database import get_db_connection

router = APIRouter()


def _normalize_confidence_0_100(v: Any) -> float:
    """Normalize any scale to 0-100 for frontend display."""
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return 0.0
    # Heuristic: <=1.0 is 0-1 scale, >1 is already 0-100
    if 0 <= f <= 1:
        return round(f * 100, 1)
    return round(f, 1)


def _row_to_lead(row: dict) -> dict:
    d = dict(row)
    # Normalize aliases for frontend compatibility
    if "kanban_status" not in d or not d.get("kanban_status"):
        d["kanban_status"] = d.get("status", "NEW")
    if "status" not in d or not d.get("status"):
        d["status"] = d.get("kanban_status", "NEW")
    # tags stored as JSON string
    tags = d.get("tags", "[]")
    if isinstance(tags, str):
        try:
            d["tags"] = json.loads(tags) if tags else []
        except Exception:
            d["tags"] = []
    if d.get("tags") is None:
        d["tags"] = []
    # confidence: keep raw 0-1 scores intact, expose normalized 0-100 display value
    # Backend stores match_score/match_confidence 0-1 and confidence_score 0-100.
    try:
        raw = d.get("match_score", 0) or d.get("match_confidence", 0) or 0
        raw_f = float(raw or 0)
    except (TypeError, ValueError):
        raw_f = 0.0
    d["match_score"] = raw_f if raw_f <= 1 else round(raw_f / 100, 4)
    d["match_confidence"] = d["match_score"]
    d["confidence_score"] = _normalize_confidence_0_100(d.get("confidence_score", 0) or raw_f)
    if not d.get("author_name") and d.get("author"):
        d["author_name"] = d.get("author")
    if not d.get("author") and d.get("author_name"):
        d["author"] = d.get("author_name")
    return d


@router.get("/")
async def list_leads(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    profile_id: Optional[int] = None,
    persona_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List leads with filters."""
    pid = profile_id if profile_id is not None else persona_id
    async with get_db_connection() as conn:
        query = "SELECT * FROM leads WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND (kanban_status = ? OR status = ?)"
            params.extend([status, status])
        if platform:
            query += " AND LOWER(platform) = ?"
            params.append(platform.lower())
        if pid:
            query += " AND (search_profile_id = ? OR profile_id = ?)"
            params.extend([pid, pid])
        if search:
            query += " AND (title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\' OR author LIKE ? ESCAPE '\\' OR company LIKE ? ESCAPE '\\')"
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{escaped}%"
            params.extend([like, like, like, like])

        cur = await conn.execute(f"SELECT COUNT(*) as cnt FROM ({query})", params)
        crow = await cur.fetchone()
        total = crow["cnt"] if crow else 0

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])

        cur = await conn.execute(query, params)
        rows = await cur.fetchall()
        items = [_row_to_lead(r) for r in rows]

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page else 0,
        }


@router.get("/export/csv")
async def export_leads_csv():
    """Export all leads as CSV (streamed in chunks)."""
    async def _gen():
        # Stream header first, then rows in batches to avoid loading whole table
        batch_size = 500
        offset = 0
        header_written = False
        fieldnames: list[str] = []
        async with get_db_connection() as conn:
            while True:
                cur = await conn.execute(
                    "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (batch_size, offset),
                )
                rows = await cur.fetchall()
                if not rows:
                    break
                dict_rows = [_row_to_lead(r) for r in rows]
                for r in dict_rows:
                    if isinstance(r.get("tags"), list):
                        r["tags"] = ",".join(str(t) for t in r["tags"])
                    if not header_written:
                        fieldnames = list(r.keys())
                        buf = io.StringIO()
                        writer = csv.DictWriter(buf, fieldnames=fieldnames)
                        writer.writeheader()
                        yield buf.getvalue()
                        header_written = True
                    buf = io.StringIO()
                    writer = csv.DictWriter(buf, fieldnames=fieldnames)
                    writer.writerow(r)
                    yield buf.getvalue()
                offset += batch_size
                if len(rows) < batch_size:
                    break
        if not header_written:
            yield "id,title,platform,url,author,content,tags,confidence_score\n"

    return StreamingResponse(
        _gen(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/{id}")
async def get_lead(id: int) -> dict[str, Any]:
    """Get lead detail with activities and drafts."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM leads WHERE id = ?", (id,))
        lead_row = await cur.fetchone()
        if not lead_row:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = _row_to_lead(lead_row)

        cur = await conn.execute(
            "SELECT * FROM lead_activities WHERE lead_id = ? ORDER BY created_at DESC", (id,)
        )
        lead["activities"] = [dict(r) for r in await cur.fetchall()]

        cur = await conn.execute(
            "SELECT * FROM ai_drafts WHERE lead_id = ? ORDER BY created_at DESC", (id,)
        )
        lead["drafts"] = [dict(r) for r in await cur.fetchall()]

        return lead


VALID_KANBAN_STATUSES = {"NEW", "CONTACTED", "INTERVIEWING", "CLOSED_WON", "CLOSED_LOST",
                         "APPLIED", "OFFER", "REJECTED",
                         "PROSPECTS", "NEGOTIATING", "CLOSED",
                         "LEADS", "QUALIFIED", "PROPOSAL", "WON", "LOST",
                         "INBOX"}


def _validate_status(status: str) -> str:
    s = str(status or "").strip()
    if not s:
        raise HTTPException(status_code=422, detail="status must not be empty")
    # Allow known statuses case-insensitively, but persist uppercased canonical form
    # to keep GROUP BY stable. Unknown custom statuses are rejected to avoid fragmentation.
    if s.upper() not in VALID_KANBAN_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status '{s}'. Allowed: {sorted(VALID_KANBAN_STATUSES)}")
    return s.upper()


@router.patch("/{id}/status")
async def update_lead_status(id: int, status: str = Body(..., embed=True)) -> dict[str, Any]:
    """Update kanban status."""
    status = _validate_status(status)
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT status, kanban_status FROM leads WHERE id = ?", (id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")

        old_status = row["kanban_status"] or row["status"]
        await conn.execute(
            "UPDATE leads SET kanban_status = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, status, id),
        )
        await conn.execute(
            "INSERT INTO lead_activities (lead_id, activity_type, description) VALUES (?, ?, ?)",
            (id, "status_change", f"Status changed from {old_status} to {status}"),
        )
        await conn.commit()
    return await get_lead(id)


@router.patch("/{id}/notes")
async def update_lead_notes(id: int, notes: str = Body(..., embed=True)) -> dict[str, Any]:
    """Update notes."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM leads WHERE id = ?", (id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")
        await conn.execute("UPDATE leads SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (notes, id))
        await conn.commit()
    return await get_lead(id)


@router.patch("/{id}/priority")
async def update_lead_priority(id: int, priority: int = Body(..., ge=1, le=5, embed=True)) -> dict[str, Any]:
    """Update priority."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM leads WHERE id = ?", (id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")
        await conn.execute("UPDATE leads SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (priority, id))
        await conn.commit()
    return await get_lead(id)


@router.patch("/{id}")
async def update_lead_generic(id: int, payload: dict = Body(...)) -> dict[str, Any]:
    """Generic update (notes / status / priority) for frontend compat."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM leads WHERE id = ?", (id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")
        if "notes" in payload:
            await conn.execute("UPDATE leads SET notes = ? WHERE id = ?", (payload["notes"], id))
        if "priority" in payload:
            try:
                pv = int(payload["priority"])
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail="priority must be an integer 1-5")
            if not 1 <= pv <= 5:
                raise HTTPException(status_code=422, detail="priority must be between 1 and 5")
            await conn.execute("UPDATE leads SET priority = ? WHERE id = ?", (pv, id))
        status_val = payload.get("kanban_status") or payload.get("status")
        if status_val:
            status_val = _validate_status(status_val)
            await conn.execute(
                "UPDATE leads SET kanban_status = ?, status = ? WHERE id = ?",
                (status_val, status_val, id),
            )
        await conn.commit()
    return await get_lead(id)


@router.delete("/{id}")
async def delete_lead(id: int) -> dict[str, Any]:
    """Delete lead and associated data."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM leads WHERE id = ?", (id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")
        # Delete children first so PRAGMA foreign_keys=ON never blocks the parent delete
        await conn.execute("DELETE FROM lead_activities WHERE lead_id = ?", (id,))
        await conn.execute("DELETE FROM ai_drafts WHERE lead_id = ?", (id,))
        await conn.execute("DELETE FROM leads WHERE id = ?", (id,))
        await conn.commit()
        return {"success": True}
