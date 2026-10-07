import asyncio
import time
from typing import Dict

class RateLimiter:
    """Per-platform rate tracking to prevent getting banned."""
    
    def __init__(self):
        # Default limits as requested
        self.limits: Dict[str, Dict[str, int]] = {
            "REDDIT": {"requests": 4, "window": 60},
            "HACKERNEWS": {"requests": 20, "window": 60},
            "LINKEDIN": {"requests": 3, "window": 60},
            "TWITTER": {"requests": 10, "window": 60},
            "THREADS": {"requests": 10, "window": 60}
        }
        self.tracking: Dict[str, list[float]] = {k: [] for k in self.limits.keys()}
        self.lock = asyncio.Lock()

    async def acquire(self, platform: str) -> bool:
        """Returns True if the request is allowed immediately."""
        platform = platform.upper()
        if platform not in self.limits:
            return True
            
        limit = self.limits[platform]["requests"]
        window = self.limits[platform]["window"]
        
        async with self.lock:
            now = time.time()
            # Clean up old timestamps
            self.tracking[platform] = [t for t in self.tracking[platform] if now - t < window]
            
            if len(self.tracking[platform]) < limit:
                self.tracking[platform].append(now)
                return True
            return False

    async def wait_if_needed(self, platform: str, timeout: float = 60.0) -> None:
        """Sleeps if rate limited until a slot is available (bounded)."""
        platform = platform.upper()
        if platform not in self.limits:
            return

        start = time.time()
        delay = 0.5
        while True:
            if await self.acquire(platform):
                return
            if (time.time() - start) >= timeout:
                return
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)


_shared_limiter: "RateLimiter | None" = None


def get_shared_limiter() -> "RateLimiter":
    global _shared_limiter
    if _shared_limiter is None:
        _shared_limiter = RateLimiter()
    return _shared_limiter
