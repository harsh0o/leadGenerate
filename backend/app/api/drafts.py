from fastapi import APIRouter, HTTPException
from typing import Any, Optional
from pydantic import BaseModel

from app.database import get_db_connection

router = APIRouter()


VALID_DRAFT_TYPES = {"COLD_DM", "COVER_LETTER", "FOLLOW_UP", "PROPOSAL", "COLD_EMAIL"}
VALID_TONES = {"PROFESSIONAL", "FRIENDLY", "CASUAL", "FORMAL", "PERSUASIVE", "CONCISE"}


class DraftGenerateBody(BaseModel):
    lead_id: int
    draft_type: Optional[str] = "COLD_DM"
    type: Optional[str] = None
    tone: Optional[str] = "PROFESSIONAL"
    custom_instructions: Optional[str] = None
    instructions: Optional[str] = None


@router.post("/generate")
async def generate_draft(body: DraftGenerateBody) -> dict[str, Any]:
    """Generate AI draft for a lead."""
    from app.config import get_settings
    from app.ai.openrouter_client import OpenRouterClient
    from app.ai.draft_generator import DraftGenerator

    lead_id = body.lead_id
    draft_type = str(body.type or body.draft_type or "COLD_DM").strip().upper().replace(" ", "_")
    tone = str(body.tone or "PROFESSIONAL").strip().upper()
    if draft_type not in VALID_DRAFT_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid draft_type '{draft_type}'. Allowed: {sorted(VALID_DRAFT_TYPES)}")
    if tone not in VALID_TONES:
        raise HTTPException(status_code=422, detail=f"Invalid tone '{tone}'. Allowed: {sorted(VALID_TONES)}")
    custom_instructions = body.custom_instructions if body.custom_instructions is not None else (body.instructions or "")

    async with get_db_connection() as conn:
        cur = await conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead_row = await cur.fetchone()
        if not lead_row:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead = dict(lead_row)

        cur = await conn.execute("SELECT persona, display_name FROM users WHERE id = 1")
        user_row = await cur.fetchone()
        persona = user_row["persona"] if user_row else "FREELANCER"
        display_name = user_row["display_name"] if user_row and user_row["display_name"] else "User"

    settings = get_settings()
    if not (settings.openrouter_api_key or "").strip():
        raise HTTPException(status_code=503, detail="OpenRouter API key not configured. Set OPENROUTER_API_KEY in backend/.env")
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        model=settings.openrouter_model,
    )
    generator = DraftGenerator(client)
    lead_summary = f"{lead.get('title','')} by {lead.get('author') or lead.get('author_name','')} at {lead.get('company','')}: {(lead.get('content') or '')[:2000]} ({lead.get('url','')})"
    try:
        content = await generator.generate(
            lead_summary=lead_summary,
            persona=persona,
            user_name=display_name,
            draft_type=draft_type,
            tone=tone,
            custom_instructions=custom_instructions,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI draft generation failed: {str(e)[:300]}")
    # Never persist failure sentinel text as a valid draft
    if not content or content.strip().lower().startswith("failed to generate draft"):
        raise HTTPException(status_code=502, detail="AI draft generation failed (empty/fallback response). Not saved.")

    async with get_db_connection() as conn:
        cur = await conn.execute(
            "INSERT INTO ai_drafts (lead_id, content, draft_type, type, tone) VALUES (?, ?, ?, ?, ?)",
            (lead_id, content, draft_type, draft_type, tone),
        )
        draft_id = cur.lastrowid
        await conn.commit()

    return {
        "id": draft_id,
        "lead_id": lead_id,
        "content": content,
        "type": draft_type,
        "draft_type": draft_type,
        "tone": tone,
    }


@router.get("/lead/{lead_id}")
async def get_drafts(lead_id: int) -> list[dict[str, Any]]:
    """Get all drafts for a lead."""
    async with get_db_connection() as conn:
        cur = await conn.execute(
            "SELECT * FROM ai_drafts WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,)
        )
        return [dict(r) for r in await cur.fetchall()]


# Back-compat alias: GET /drafts/{lead_id} historically listed drafts for a lead.
# Kept so older frontends keep working, but /lead/{lead_id} is canonical.
@router.get("/{lead_id}")
async def get_drafts_legacy(lead_id: int) -> list[dict[str, Any]]:
    """Deprecated alias for GET /lead/{lead_id}."""
    return await get_drafts(lead_id)


@router.delete("/{draft_id}")
async def delete_draft(draft_id: int) -> dict[str, Any]:
    """Delete a draft."""
    async with get_db_connection() as conn:
        cur = await conn.execute("DELETE FROM ai_drafts WHERE id = ?", (draft_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Draft not found")
        await conn.commit()
        return {"success": True}
