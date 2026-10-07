import asyncio
import random
import json
from typing import Tuple, Optional, Dict, Any, List
from loguru import logger

from app.channels.base import BaseChannel
from app.models.platform_health import HealthStatus

class LinkedInChannel(BaseChannel):
    """
    LinkedIn scraper using Playwright intercepting Voyager API.
    Created by harsh0o.
    """
    
    @property
    def platform_name(self) -> str:
        return 'linkedin'

    async def fetch_posts(self, tags: List[str], **kwargs) -> List[Dict[str, Any]]:
        # Deferred import so playwright is not strictly required at module load
        from playwright.async_api import async_playwright
        import pathlib as _pl

        def _resolve_profile_dir(raw: str) -> str:
            p = _pl.Path(raw)
            if not p.is_absolute():
                base = _pl.Path(__file__).resolve().parent.parent.parent
                return str(base / raw)
            return raw

        posts = []
        try:
            async with async_playwright() as p:
                profile_dir = _resolve_profile_dir(getattr(self.settings, "linkedin_profile_dir", "./linkedin_chrome_profile"))
                headless = getattr(self.settings, "linkedin_headless", True)
                
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=headless,
                    args=["--disable-blink-features=AutomationControlled"],
                    user_agent=getattr(self.settings, "linkedin_user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                )
                
                page = await context.new_page()
                
                intercepted_data = []

                async def handle_response(response):
                    if "voyager/api/graphql" in response.url and "jobs" in response.url.lower():
                        try:
                            body = await response.text()
                            data = json.loads(body)
                            intercepted_data.append(data)
                        except Exception as e:
                            logger.debug(f"Could not parse voyager response: {e}")

                page.on("response", handle_response)
                
                query = " ".join(tags) if tags else "hiring"
                url = f"https://www.linkedin.com/jobs/search/?keywords={query}&f_TPR=r86400"
                
                await self.rate_limiter.wait_if_needed('linkedin')
                await page.goto(url, wait_until="networkidle")
                
                # Human-like actions
                await asyncio.sleep(random.uniform(3, 6))
                for _ in range(3):
                    await page.mouse.wheel(0, 1000)
                    await asyncio.sleep(random.uniform(1, 3))
                
                try:
                    await context.close()
                except Exception:
                    pass

                # Process intercepted data (deterministic IDs via content hash so dedup works)
                import hashlib as _hashlib
                for data in intercepted_data:
                    blob = json.dumps(data, sort_keys=True)[:2000]
                    digest = _hashlib.sha256(f"{query}|{blob}".encode("utf-8")).hexdigest()[:16]
                    text_snippet = blob[:500]
                    posts.append(self._build_raw_post(
                        platform_post_id=f"li_{digest}",
                        author="LinkedIn Job",
                        title=f"Matched job for {query}",
                        body=text_snippet,
                        url=url
                    ))

        except Exception as e:
            logger.error(f"Error fetching LinkedIn posts: {e}")

        return posts

    async def health_check(self) -> Tuple[HealthStatus, Optional[str]]:
        from playwright.async_api import async_playwright
        import pathlib as _pl

        def _resolve_profile_dir(raw: str) -> str:
            p = _pl.Path(raw)
            if not p.is_absolute():
                base = _pl.Path(__file__).resolve().parent.parent.parent
                return str(base / raw)
            return raw

        context = None
        try:
            async with async_playwright() as p:
                profile_dir = _resolve_profile_dir(getattr(self.settings, "linkedin_profile_dir", "./linkedin_chrome_profile"))
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=True,
                    user_agent=getattr(self.settings, "linkedin_user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = await context.new_page()
                await page.goto("https://www.linkedin.com/feed/", timeout=15000)
                # Guard against login-wall false-positives: must actually land on feed
                # with a recognizable marker, not a login/checkpoint redirect.
                final_url = (page.url or "")
                if "linkedin.com/feed" not in final_url and "linkedin.com/in" not in final_url:
                    raise RuntimeError(f"LinkedIn health check did not reach feed (at {final_url[:120]})")
                await context.close()
                context = None
            return HealthStatus.HEALTHY, None
        except Exception as e:
            try:
                if context is not None:
                    await context.close()
            except Exception:
                pass
            return HealthStatus.DOWN, str(e)[:500]

