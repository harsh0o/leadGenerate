import httpx
from typing import Tuple, Optional, Dict, Any, List
from loguru import logger
from urllib.parse import quote_plus

from app.channels.base import BaseChannel
from app.models.platform_health import HealthStatus

class RedditChannel(BaseChannel):
    """
    Reddit scraper channel using JSON endpoints.
    Created by harsh0o.
    """
    
    TARGET_SUBREDDITS = ['forhire', 'hiring', 'freelance', 'remotejs', 'jobbit', 'techjobs']
    
    @property
    def platform_name(self) -> str:
        return 'reddit'

    async def fetch_posts(self, tags: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Fetch job posts from Reddit."""
        posts = []
        headers = {"User-Agent": getattr(self.settings, "reddit_user_agent", "LeadHunter AI (by harsh0o) / 1.0")}
        query = quote_plus(" OR ".join(tags)) if tags else quote_plus("hiring")
        
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            for sub in self.TARGET_SUBREDDITS:
                try:
                    await self.rate_limiter.wait_if_needed('reddit')
                    url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&sort=new&limit=25"
                    
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post_data = child.get("data", {})
                        if post_data.get("name"): # t3_...
                            post = self._build_raw_post(
                                platform_post_id=post_data.get("name"),
                                author=post_data.get("author", ""),
                                title=post_data.get("title", ""),
                                body=post_data.get("selftext", ""),
                                url=f"https://reddit.com{post_data.get('permalink', '')}"
                            )
                            posts.append(post)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 403):
                        logger.warning(f"Reddit rate limited or forbidden on sub {sub}: {e}")
                    else:
                        logger.error(f"HTTP error fetching Reddit posts for {sub}: {e}")
                except Exception as e:
                    logger.error(f"Error fetching Reddit posts for {sub}: {e}")
        
        return posts

    async def health_check(self) -> Tuple[HealthStatus, Optional[str]]:
        """Test Reddit connectivity."""
        headers = {"User-Agent": getattr(self.settings, "reddit_user_agent", "LeadHunter AI (by harsh0o) / 1.0")}
        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                response = await client.get("https://www.reddit.com/r/forhire/hot.json?limit=1")
                response.raise_for_status()
                return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.DOWN, str(e)

