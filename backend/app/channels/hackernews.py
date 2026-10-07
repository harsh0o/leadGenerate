import asyncio
import httpx
from typing import Tuple, Optional, Dict, Any, List
from loguru import logger

from app.channels.base import BaseChannel
from app.models.platform_health import HealthStatus

class HackerNewsChannel(BaseChannel):
    """
    HackerNews scraper channel using Firebase and Algolia APIs.
    Created by harsh0o.
    """
    
    HN_API_BASE = 'https://hacker-news.firebaseio.com/v0'
    ALGOLIA_API = 'https://hn.algolia.com/api/v1'
    
    @property
    def platform_name(self) -> str:
        return 'hackernews'

    async def _fetch_item(self, client: httpx.AsyncClient, item_id: int, sem: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
        async with sem:
            try:
                await self.rate_limiter.wait_if_needed('hackernews')
                response = await client.get(f"{self.HN_API_BASE}/item/{item_id}.json")
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"HN Item fetch error for {item_id}: {e}")
        return None

    async def fetch_posts(self, tags: List[str], **kwargs) -> List[Dict[str, Any]]:
        posts = []
        sem = asyncio.Semaphore(5)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await self.rate_limiter.wait_if_needed('hackernews')
                
                # Strategy 1: Algolia Search for tags in 'who is hiring' or general job stories
                # NOTE: Algolia `query=` is a single free-text query - it does not parse
                # an "OR" operator, so issue one query per tag and merge hits.
                from urllib.parse import quote_plus as _qp
                from collections import OrderedDict as _OD
                tag_queries = [t for t in (tags or []) if str(t).strip()] or ["hiring"]
                merged_hits = _OD()
                for tq in tag_queries[:5]:
                    search_url = f"{self.ALGOLIA_API}/search?tags=comment&query={_qp(str(tq))}"
                    await self.rate_limiter.wait_if_needed('hackernews')
                    search_resp = await client.get(search_url)

                    if search_resp.status_code == 200:
                        for hit in search_resp.json().get("hits", []):
                            oid = str(hit.get("objectID") or "")
                            if oid and oid not in merged_hits:
                                merged_hits[oid] = hit
                for hit in merged_hits.values():
                        posts.append(self._build_raw_post(
                            platform_post_id=str(hit.get("objectID")),
                            author=hit.get("author", ""),
                            title=hit.get("story_title", ""),
                            body=hit.get("comment_text", ""),
                            url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        ))

                # Strategy 2: Firebase API for direct jobstories
                jobs_resp = await client.get(f"{self.HN_API_BASE}/jobstories.json")
                if jobs_resp.status_code == 200:
                    raw_ids = jobs_resp.json()
                    job_ids = (raw_ids[:30] if isinstance(raw_ids, list) else [])  # limit to top 30 recent jobs
                    
                    tasks = [self._fetch_item(client, j_id, sem) for j_id in job_ids]
                    job_items = await asyncio.gather(*tasks)
                    
                    for item in job_items:
                        if item and not item.get("deleted") and not item.get("dead"):
                            posts.append(self._build_raw_post(
                                platform_post_id=str(item.get("id")),
                                author=item.get("by", ""),
                                title=item.get("title", ""),
                                body=item.get("text", ""),
                                url=item.get("url", f"https://news.ycombinator.com/item?id={item.get('id')}")
                            ))
                            
            except Exception as e:
                logger.error(f"Error fetching HN posts: {e}")
                
        return posts

    async def health_check(self) -> Tuple[HealthStatus, Optional[str]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.HN_API_BASE}/maxitem.json")
                response.raise_for_status()
                if isinstance(response.json(), int):
                    return HealthStatus.HEALTHY, None
                return HealthStatus.DOWN, "Invalid response type"
        except Exception as e:
            return HealthStatus.DOWN, str(e)

