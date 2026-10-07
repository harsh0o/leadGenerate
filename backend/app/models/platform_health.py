from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from .scan_job import Platform

class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"

class PlatformHealthBase(BaseModel):
    platform: Platform
    status: HealthStatus
    error_detail: Optional[str] = None
    consecutive_failures: int = 0

class PlatformHealth(PlatformHealthBase):
    last_check_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
