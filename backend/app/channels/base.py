from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import datetime

from app.config import Settings
from app.utils.rate_limiter import RateLimiter
from app.models.platform_health import HealthStatus

class BaseChannel(ABC):
    """
    Abstract BaseChannel class for LeadHunter AI.
    Created by harsh0o.
    """
    
    def __init__(self, settings: Settings, rate_limiter: RateLimiter):
        self.settings = settings
        self.rate_limiter = rate_limiter

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the platform name (e.g., 'reddit', 'linkedin')"""
        pass

    @abstractmethod
    async def fetch_posts(self, tags: list[str], **kwargs) -> list[Dict[str, Any]]:
        """
        Fetch raw posts from the platform based on tags.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Tuple[HealthStatus, Optional[str]]:
        """
        Test connectivity to the platform.
        """
        pass

    def _build_raw_post(
        self, 
        platform_post_id: str, 
        author: str, 
        title: str, 
        body: str, 
        url: str
    ) -> Dict[str, Any]:
        """
        Helper method to standardize raw post dictionaries.
        """
        return {
            "platform": self.platform_name,
            "platform_post_id": str(platform_post_id),
            "author": author or "Unknown",
            "title": title or "",
            "body": body or "",
            "url": url or "",
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

