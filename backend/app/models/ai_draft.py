from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class DraftType(str, Enum):
    COLD_DM = "COLD_DM"
    COVER_LETTER = "COVER_LETTER"
    EMAIL = "EMAIL"
    CUSTOM = "CUSTOM"

class Tone(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    CASUAL = "CASUAL"
    TECHNICAL = "TECHNICAL"

class DraftRequest(BaseModel):
    lead_id: str
    draft_type: DraftType
    tone: Tone = Tone.PROFESSIONAL
    custom_instructions: Optional[str] = None

class AIDraftBase(BaseModel):
    lead_id: str
    draft_type: DraftType
    content: str
    tone: Optional[Tone] = None

class AIDraft(AIDraftBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
