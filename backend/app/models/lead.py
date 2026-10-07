from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class KanbanStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    INTERVIEWING = "INTERVIEWING"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"

class LeadBase(BaseModel):
    raw_post_id: str
    search_profile_id: str
    status: KanbanStatus = KanbanStatus.NEW
    match_score: Optional[float] = None
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: Optional[KanbanStatus] = None
    notes: Optional[str] = None

class Lead(LeadBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LeadActivity(BaseModel):
    id: str
    lead_id: str
    activity_type: str
    description: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LeadWithActivities(Lead):
    activities: List[LeadActivity] = []
