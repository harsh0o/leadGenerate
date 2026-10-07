from fastapi import APIRouter, HTTPException, Body
from typing import Any

from app.database import get_db_connection

router = APIRouter()


@router.get("/")
async def get_user_settings() -> dict[str, Any]:
    """Get all settings for default user."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM users WHERE id = 1")
        row = await cur.fetchone()
        if not row:
            await conn.execute(
                "INSERT INTO users (id, display_name, persona) VALUES (1, 'Admin', 'FREELANCER')"
            )
            await conn.commit()
            cur = await conn.execute("SELECT * FROM users WHERE id = 1")
            row = await cur.fetchone()
        return dict(row) if row else {}


VALID_PERSONAS = {"JOB_HUNTER", "FREELANCER", "AGENCY"}


def _validate_persona(v: Any) -> str:
    s = str(v or "").strip().upper()
    if s not in VALID_PERSONAS:
        raise HTTPException(status_code=422, detail=f"Invalid persona '{v}'. Allowed: {sorted(VALID_PERSONAS)}")
    return s


SECRET_KEY_HINTS = ("key", "token", "secret", "password", "auth")


def _mask_value(k: str, v: Any) -> Any:
    kl = k.lower()
    if any(h in kl for h in SECRET_KEY_HINTS) and isinstance(v, str) and len(v) > 8:
        return v[:4] + "****" + v[-3:]
    return v


# Keys that may be written via /platforms (allowlist to avoid arbitrary settings injection)
ALLOWED_PLATFORM_KEYS = {
    "twitter_auth_token", "rsshub_base_url", "reddit_user_agent",
    "linkedin_profile_dir", "openrouter_api_key", "openrouter_model",
}


@router.put("/")
async def update_settings(payload: dict = Body(...)) -> dict[str, Any]:
    """Bulk update settings (validated)."""
    allowed = {"display_name", "email", "persona"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if "persona" in updates:
        updates["persona"] = _validate_persona(updates["persona"])
    if updates:
        async with get_db_connection() as conn:
            cur = await conn.execute("SELECT id FROM users WHERE id = 1")
            if not await cur.fetchone():
                await conn.execute(
                    "INSERT INTO users (id, display_name, persona) VALUES (1, 'Admin', 'FREELANCER')"
                )
            sets = ", ".join(f"{k} = ?" for k in updates)
            await conn.execute(
                f"UPDATE users SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
                list(updates.values()),
            )
            await conn.commit()
    row = await get_user_settings()
    # Mask nothing in users table (no secrets there), but keep shape stable
    return row


@router.put("/persona")
async def update_persona(persona: str = Body(..., embed=True)) -> dict[str, Any]:
    """Change active persona (validated)."""
    persona = _validate_persona(persona)
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM users WHERE id = 1")
        if not await cur.fetchone():
            await conn.execute(
                "INSERT INTO users (id, display_name, persona) VALUES (1, 'Admin', 'FREELANCER')"
            )
        await conn.execute("UPDATE users SET persona = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (persona,))
        await conn.commit()
    return await get_user_settings()


@router.put("/platforms")
async def configure_platforms(config: dict = Body(...)) -> dict[str, Any]:
    """Configure platform credentials (allowlisted, JSON-encoded)."""
    import json as _json
    unknown = [k for k in config.keys() if k not in ALLOWED_PLATFORM_KEYS]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown settings keys: {unknown}. Allowed: {sorted(ALLOWED_PLATFORM_KEYS)}")
    async with get_db_connection() as conn:
        for k, v in config.items():
            val = _json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
                (k, val),
            )
        await conn.commit()
    return {"success": True, "message": "Credentials updated"}


@router.get("/platforms")
async def get_platform_settings() -> dict[str, Any]:
    """Read non-secret platform settings with secrets masked."""
    import json as _json
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT key, value FROM settings")
        out: dict[str, Any] = {}
        for r in await cur.fetchall():
            raw = r["value"]
            try:
                parsed = _json.loads(raw)
            except Exception:
                parsed = raw
            out[r["key"]] = _mask_value(r["key"], parsed)
        return out


@router.post("/init")
async def init_user() -> dict[str, Any]:
    """Initialize default user if not exists."""
    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT id FROM users WHERE id = 1")
        if not await cur.fetchone():
            await conn.execute(
                "INSERT INTO users (id, display_name, persona) VALUES (1, 'Admin', 'FREELANCER')"
            )
            await conn.commit()
    return await get_user_settings()
