from loguru import logger
from typing import Optional, List
from app.ai.openrouter_client import OpenRouterClient
from app.ai.prompts import TAG_MATCHER_SYSTEM_PROMPT, TAG_MATCHER_USER_TEMPLATE
from app.models.raw_post import TagMatchResult, ExtractedLead, MatchLevel, _to_float_or_none

class TagMatcher:
    """
    Agent 2: Matches tags and extracts structured fields.
    Created by harsh0o.
    """
    def __init__(self, client: OpenRouterClient):
        self.client = client

    async def match(
        self, 
        post_text: str, 
        tags: List[str], 
        min_budget: Optional[float], 
        location_pref: Optional[str], 
        remote_only: bool
    ) -> TagMatchResult:
        
        user_msg = TAG_MATCHER_USER_TEMPLATE.format(
            post_text=post_text,
            user_tags=", ".join(tags),
            min_budget=str(min_budget) if min_budget else "None",
            location_pref=location_pref or "None",
            remote_only=str(remote_only)
        )
        
        try:
            resp = await self.client.chat_completion(
                system_prompt=TAG_MATCHER_SYSTEM_PROMPT,
                user_message=user_msg,
                temperature=0.1
            )
            
            if "match_level" in resp:
                raw_level = str(resp["match_level"]).strip().upper().replace("-", "_").replace(" ", "_")
                try:
                    match_level = MatchLevel(raw_level)
                except ValueError:
                    match_level = MatchLevel.NO_MATCH
                extracted_data = resp.get("extracted_lead") or resp.get("extracted") or {}

                try:
                    conf = float(resp.get("confidence", 0.0))
                except (TypeError, ValueError):
                    conf = 0.0
                conf = max(0.0, min(1.0, conf))
                extracted = ExtractedLead(
                    company=extracted_data.get("company") or extracted_data.get("company_name"),
                    title=extracted_data.get("title") or extracted_data.get("role"),
                    budget_min=_to_float_or_none(extracted_data.get("budget_min", extracted_data.get("budget"))),
                    budget_max=_to_float_or_none(extracted_data.get("budget_max", extracted_data.get("budget"))),
                    currency=extracted_data.get("currency") or "USD",
                    location=extracted_data.get("location"),
                    is_remote=bool(extracted_data.get("is_remote", False)),
                    summary=str(resp.get("reasoning", "") or "")[:500],
                )

                raw_matched = resp.get("matched_tags", []) or []
                raw_missing = resp.get("missing_tags", []) or []
                result = TagMatchResult(
                    match_level=match_level,
                    confidence=conf,
                    matched_tags=[str(t) for t in raw_matched] if isinstance(raw_matched, list) else [],
                    missing_tags=[str(t) for t in raw_missing] if isinstance(raw_missing, list) else [],
                    extracted=extracted,
                    reasoning=str(resp.get("reasoning", "") or ""),
                )
                return result
                
        except Exception as e:
            logger.error(f"Error in TagMatcher: {e}")
            
        return TagMatchResult(
            match_level=MatchLevel.NO_MATCH, 
            confidence=0.0, 
            matched_tags=[], 
            missing_tags=[],
            reasoning="Parsing failed.",
            extracted=None
        )

    def is_passing(self, result: TagMatchResult, threshold: float = 0.85) -> bool:
        return result.match_level == MatchLevel.FULL_MATCH and result.confidence >= threshold
