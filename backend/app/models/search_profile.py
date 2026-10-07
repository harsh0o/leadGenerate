from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TagType(str, Enum):
    SKILL = "SKILL"
    ROLE = "ROLE"
    INDUSTRY = "INDUSTRY"
    KEYWORD = "KEYWORD"

class ProfileTagBase(BaseModel):
    tag: str
    tag_type: TagType

class ProfileTag(ProfileTagBase):
    id: str
    search_profile_id: str
    
    model_config = ConfigDict(from_attributes=True)

class SearchProfileBase(BaseModel):
    name: str
    location_pref: Optional[str] = None
    remote_only: bool = False
    min_budget: Optional[float] = None
    currency: Optional[str] = None
    is_active: bool = True

class SearchProfileCreate(SearchProfileBase):
    user_id: str
    tags: List[ProfileTagBase]

class SearchProfileUpdate(BaseModel):
    name: Optional[str] = None
    location_pref: Optional[str] = None
    remote_only: Optional[bool] = None
    min_budget: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[ProfileTagBase]] = None

class SearchProfile(SearchProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
