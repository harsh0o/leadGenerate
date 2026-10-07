from fastapi import APIRouter, HTTPException, Body
import json
from typing import Any, Optional

from app.database import get_db_connection

router = APIRouter()


async def _get_profile(conn, pid: int) -> dict[str, Any]:
    cur = await conn.execute("SELECT * FROM search_profiles WHERE id = ?", (pid,))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = dict(row)
    # tags
    cur = await conn.execute(
        "SELECT tag, tag_type FROM profile_tags WHERE search_profile_id = ? OR profile_id = ?",
        (pid, pid),
    )
    tag_rows = await cur.fetchall()
    profile["tags"] = [{"name": r["tag"], "type": r["tag_type"]} for r in tag_rows]
    # normalize platform list
    plats = profile.get("platforms", "")
    if isinstance(plats, str) and plats:
        try:
            profile["platforms"] = json.loads(plats)
        except Exception:
            profile["platforms"] = [p.strip() for p in plats.split(",") if p.strip()]
    else:
        profile["platforms"] = plats or []
    return profile


@router.get("/")
async def list_profiles() -> list[dict[str, Any]]:
    """List all profiles with their tags."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM search_profiles ORDER BY created_at DESC")
        profiles = [dict(r) for r in await cur.fetchall()]
        out = []
        for p in profiles:
            cur2 = await conn.execute(
                "SELECT tag, tag_type FROM profile_tags WHERE search_profile_id = ? OR profile_id = ?",
                (p["id"], p["id"]),
            )
            tag_rows = await cur2.fetchall()
            p["tags"] = [{"name": r["tag"], "type": r["tag_type"]} for r in tag_rows]
            plats = p.get("platforms", "")
            if isinstance(plats, str) and plats:
                try:
                    p["platforms"] = json.loads(plats)
                except Exception:
                    p["platforms"] = [x.strip() for x in plats.split(",") if x.strip()]
            out.append(p)
    return out


@router.post("/")
async def create_profile(payload: dict = Body(...)) -> dict[str, Any]:
    """Create profile with nested tags. Supports both API.md and frontend shapes."""
    name = payload.get("name", "Untitled")
    description = payload.get("description", "")
    tags_in = payload.get("tags", [])
    # tags may be list[str] or list[{name/tag, type}]
    norm_tags: list[tuple[str, str]] = []
    for t in tags_in:
        if isinstance(t, str):
            norm_tags.append((t, "KEYWORD"))
        elif isinstance(t, dict):
            norm_tags.append((t.get("name") or t.get("tag", ""), t.get("type") or t.get("tag_type", "KEYWORD")))
    location = payload.get("location") or payload.get("location_pref", "")
    budget_min = payload.get("budget_min", payload.get("min_budget"))
    budget_max = payload.get("budget_max", payload.get("max_budget"))
    try:
        budget_min = float(budget_min) if budget_min not in (None, "") else None
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="budget_min must be numeric")
    try:
        budget_max = float(budget_max) if budget_max not in (None, "") else None
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="budget_max must be numeric")
    currency = str(payload.get("currency", "USD") or "USD")[:8]
    is_active = 1 if payload.get("is_active", True) else 0
    remote_only = 1 if payload.get("remote_only") else 0
    platforms = payload.get("platforms", ["reddit", "hackernews"])
    if isinstance(platforms, list):
        platforms = [str(p).lower() for p in platforms if str(p).strip()]
        platforms_json = json.dumps(platforms or ["reddit", "hackernews"])
    else:
        platforms_json = json.dumps(["reddit", "hackernews"])

    async with get_db_connection() as conn:
        cur = await conn.execute(
            """INSERT INTO search_profiles
               (user_id, name, description, location_pref, location, remote_only, min_budget, budget_min, budget_max, currency, platforms, is_active)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, location, location, remote_only, budget_min, budget_min, budget_max, currency, platforms_json, is_active),
        )
        profile_id = cur.lastrowid
        for tag_name, tag_type in norm_tags:
            if not tag_name:
                continue
            await conn.execute(
                "INSERT INTO profile_tags (search_profile_id, profile_id, tag, tag_type) VALUES (?, ?, ?, ?)",
                (profile_id, profile_id, tag_name, tag_type),
            )
        await conn.commit()
        return await _get_profile(conn, profile_id)


@router.get("/{id}")
async def get_profile(id: int) -> dict[str, Any]:
    """Get single profile with tags."""
    async with get_db_connection() as conn:
        return await _get_profile(conn, id)


@router.put("/{id}")
async def update_profile(id: int, payload: dict = Body(...)) -> dict[str, Any]:
    """Update profile."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM search_profiles WHERE id = ?", (id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Profile not found")

        fields: list[str] = []
        vals: list[Any] = []
        if "name" in payload:
            fields.append("name = ?")
            vals.append(payload["name"])
        if "description" in payload:
            fields.append("description = ?")
            vals.append(payload["description"])
        if "location" in payload or "location_pref" in payload:
            loc = payload.get("location", payload.get("location_pref"))
            fields += ["location = ?", "location_pref = ?"]
            vals += [loc, loc]
        for k in ("remote_only", "is_active"):
            if k in payload:
                fields.append(f"{k} = ?")
                vals.append(1 if payload[k] else 0)
        for k in ("budget_min", "min_budget"):
            if k in payload:
                try:
                    bv = float(payload[k]) if payload[k] not in (None, "") else None
                except (TypeError, ValueError):
                    raise HTTPException(status_code=422, detail=f"{k} must be numeric")
                fields += ["budget_min = ?", "min_budget = ?"]
                vals += [bv, bv]
                break
        if "budget_max" in payload or "max_budget" in payload:
            raw_bmax = payload.get("budget_max", payload.get("max_budget"))
            try:
                bmax = float(raw_bmax) if raw_bmax not in (None, "") else None
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail="budget_max must be numeric")
            fields.append("budget_max = ?")
            vals.append(bmax)
        if "currency" in payload:
            fields.append("currency = ?")
            vals.append(str(payload["currency"] or "USD")[:8])
        if "platforms" in payload and isinstance(payload["platforms"], list):
            plats = [str(p).lower() for p in payload["platforms"] if str(p).strip()]
            fields.append("platforms = ?")
            vals.append(json.dumps(plats))
        if fields:
            vals.append(id)
            await conn.execute(f"UPDATE search_profiles SET {', '.join(fields)} WHERE id = ?", vals)

        if "tags" in payload:
            await conn.execute("DELETE FROM profile_tags WHERE search_profile_id = ? OR profile_id = ?", (id, id))
            for t in payload["tags"]:
                if isinstance(t, str):
                    tn, tt = t, "KEYWORD"
                else:
                    tn = t.get("name") or t.get("tag", "")
                    tt = t.get("type") or t.get("tag_type", "KEYWORD")
                if tn:
                    await conn.execute(
                        "INSERT INTO profile_tags (search_profile_id, profile_id, tag, tag_type) VALUES (?, ?, ?, ?)",
                        (id, id, tn, tt),
                    )
        await conn.commit()
        return await _get_profile(conn, id)


@router.delete("/{id}")
async def delete_profile(id: int) -> dict[str, Any]:
    """Delete profile (hard delete + tags)."""
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM profile_tags WHERE search_profile_id = ? OR profile_id = ?", (id, id))
        cur = await conn.execute("DELETE FROM search_profiles WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profile not found")
        await conn.commit()
        return {"success": True}


@router.patch("/{id}/toggle")
@router.put("/{id}/toggle")
async def toggle_profile(id: int, payload: Optional[dict] = Body(None)) -> dict[str, Any]:
    """Toggle is_active. Returns full profile to keep frontend state intact."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT is_active FROM search_profiles WHERE id = ?", (id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        if payload and "is_active" in payload:
            new_status = 1 if payload["is_active"] else 0
        else:
            new_status = 0 if row["is_active"] else 1
        await conn.execute("UPDATE search_profiles SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, id))
        await conn.commit()
        return await _get_profile(conn, id)
