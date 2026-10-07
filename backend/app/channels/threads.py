import hashlib
import httpx
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, Dict, Any, List
from urllib.parse import quote_plus
from loguru import logger

from app.channels.base import BaseChannel
from app.models.platform_health import HealthStatus


def _stable_id(*parts: str) -> str:
    blob = "|".join(p or "" for p in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _parse_items(payload: Any, raw_text: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [i for i in payload["items"] if isinstance(i, dict)]
    items: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(raw_text)
        for item in root.iter("item"):
            def _t(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "") if el is not None else ""
            items.append({
                "id": _t("guid") or _t("link"),
                "title": _t("title"),
                "content_html": _t("description"),
                "url": _t("link"),
                "author": _t("author") or _t("creator"),
            })
    except ET.ParseError:
        pass
    return items


async def _fetch_rsshub(client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
    resp = await client.get(url)
    if resp.status_code == 404 and not url.endswith(".json"):
        resp = await client.get(url + ".json")
    resp.raise_for_status()
    try:
        payload = resp.json()
    except Exception:
        payload = None
    if payload is not None and isinstance(payload, dict) and "items" in payload:
        return _parse_items(payload, resp.text)
    return _parse_items(None, resp.text)


class ThreadsChannel(BaseChannel):
    """
    Threads scraper channel via RSSHub.
    Created by harsh0o.
    """

    @property
    def platform_name(self) -> str:
        return 'threads'

    async def fetch_posts(self, tags: List[str], **kwargs) -> List[Dict[str, Any]]:
        posts = []
        rsshub_url = (getattr(self.settings, "rsshub_base_url", "https://rsshub.app") or "").rstrip("/")
        query = quote_plus(tags[0] if tags else "hiring")

        try:
            await self.rate_limiter.wait_if_needed('threads')
            url = f"{rsshub_url}/threads/{query}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                items = await _fetch_rsshub(client, url)

                for idx, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue
                    raw_author = item.get("author", "Unknown")
                    if isinstance(raw_author, dict):
                        author = raw_author.get("name", "Unknown") or "Unknown"
                    elif isinstance(raw_author, str):
                        author = raw_author or "Unknown"
                    else:
                        author = "Unknown"
                    title = item.get("title", "") or ""
                    body = item.get("content_html") or item.get("summary") or item.get("content") or ""
                    link = item.get("url") or item.get("link") or ""
                    pid = str(item.get("id") or link or _stable_id(title, str(body), author, str(idx)))
                    posts.append(self._build_raw_post(
                        platform_post_id=pid,
                        author=author,
                        title=title,
                        body=body,
                        url=link or ""
                    ))
        except Exception as e:
            logger.error(f"Error fetching Threads posts via RSSHub: {e}")

        return posts

    async def health_check(self) -> Tuple[HealthStatus, Optional[str]]:
        rsshub_url = (getattr(self.settings, "rsshub_base_url", "https://rsshub.app") or "").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{rsshub_url}/threads/zuck")
                response.raise_for_status()
            return HealthStatus.HEALTHY, None
        except Exception as e:
            return HealthStatus.DOWN, str(e)
