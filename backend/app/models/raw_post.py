from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .scan_job import Platform

class IntentType(str, Enum):
    OFFERING_JOB = "OFFERING_JOB"
    SEEKING_JOB = "SEEKING_JOB"
    SPAM = "SPAM"
    DISCUSSION = "DISCUSSION"
    UNCLEAR = "UNCLEAR"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            norm = value.strip().upper().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == norm:
                    return member
        return None

class MatchLevel(str, Enum):
    FULL_MATCH = "FULL_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_MATCH = "NO_MATCH"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            norm = value.strip().upper().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == norm:
                    return member
        return None

class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

def _to_float_or_none(v: object) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        import re as _re
        s = v.replace(",", "").strip()
        # Handle "$5k", "5k", "$5,000", "5.5K"
        m = _re.match(r"^\$?\s*([0-9]*\.?[0-9]+)\s*([kKmM]?)$", s)
        if m:
            num = float(m.group(1))
            suffix = m.group(2).lower()
            if suffix == "k":
                num *= 1000
            elif suffix == "m":
                num *= 1_000_000
            return num
        try:
            return float(s.lstrip("$"))
        except ValueError:
            return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class ExtractedLead(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    currency: Optional[str] = "USD"
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    contact_method: Optional[str] = None
    post_url: Optional[str] = None
    summary: Optional[str] = None

class TagMatchResult(BaseModel):
    match_level: MatchLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched_tags: List[str]
    missing_tags: List[str]
    extracted: Optional[ExtractedLead] = None
    reasoning: str

class RawPostBase(BaseModel):
    platform: Platform
    platform_post_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[datetime] = None

class RawPost(RawPostBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
