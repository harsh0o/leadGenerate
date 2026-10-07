from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum

class ScanStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Platform(str, Enum):
    REDDIT = "REDDIT"
    HACKERNEWS = "HACKERNEWS"
    LINKEDIN = "LINKEDIN"
    TWITTER = "TWITTER"
    THREADS = "THREADS"

    @classmethod
    def _missing_(cls, value: object):
        # Accept lowercase / mixed-case platform names from channels/DB
        if isinstance(value, str):
            upper = value.strip().upper()
            for member in cls:
                if member.value == upper:
                    return member
        return None

class ScanJobBase(BaseModel):
    platform: Platform

    model_config = ConfigDict(use_enum_values=False)

class ScanJobCreate(ScanJobBase):
    pass

class ScanJob(ScanJobBase):
    id: str
    status: ScanStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
