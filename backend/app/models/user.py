from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class Persona(str, Enum):
    JOB_HUNTER = "JOB_HUNTER"
    FREELANCER = "FREELANCER"
    AGENCY = "AGENCY"

class UserBase(BaseModel):
    persona: Persona
    display_name: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    id: str

class UserUpdate(BaseModel):
    persona: Optional[Persona] = None
    display_name: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
