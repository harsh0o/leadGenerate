import asyncio
import json
import uuid
from loguru import logger
from typing import List

from app.models.scan_job import ScanStatus


class ScanPipeline:
    """
    Core Orchestrator for LeadHunter AI.
    Scrape -> dedup -> AI Bouncer -> Tag Matcher -> persist Lead.
    """

    def __init__(self, settings=None, channels_map=None, intent_bouncer=None, tag_matcher=None, rate_limiter=None):
        from app.config import get_settings
        from app.utils.rate_limiter import RateLimiter
        from app.ai.openrouter_client import OpenRouterClient
        from app.ai.intent_bouncer import IntentBouncer
        from app.ai.tag_matcher import TagMatcher
        from app import channels as channels_pkg

        self.settings = settings or get_settings()
        self.rate_limiter = rate_limiter or RateLimiter()

        if channels_map is None:
            channels_map = {
                "reddit": channels_pkg.RedditChannel,
                "hackernews": channels_pkg.HackerNewsChannel,
                "linkedin": channels_pkg.LinkedInChannel,
                "twitter": channels_pkg.TwitterChannel,
                "threads": channels_pkg.ThreadsChannel,
            }
        self.channels = channels_map

        if intent_bouncer is None or tag_matcher is None:
            client = OpenRouterClient(
                api_key=getattr(self.settings, "openrouter_api_key", ""),
                base_url=getattr(self.settings, "openrouter_base_url", "https://openrouter.ai/api/v1"),
                model=getattr(self.settings, "openrouter_model", "mistralai/mistral-7b-instruct:free"),
            )
            self.intent_bouncer = intent_bouncer or IntentBouncer(client)
            self.tag_matcher = tag_matcher or TagMatcher(client)
        else:
            self.intent_bouncer = intent_bouncer
            self.tag_matcher = tag_matcher

    async def _load_profile(self, search_profile_id: int) -> dict:
        from app.database import get_db_connection

        async with get_db_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM search_profiles WHERE id = ?", (search_profile_id,)
            )
            row = await cur.fetchone()
            if not row:
                raise ValueError(f"Search profile {search_profile_id} not found")
            profile = dict(row)
            cur = await conn.execute(
                "SELECT tag FROM profile_tags WHERE search_profile_id = ? OR profile_id = ?",
                (search_profile_id, search_profile_id),
            )
            tags = [r["tag"] for r in await cur.fetchall()] or ["hiring", "developer"]
            profile["tags"] = tags
            # platforms JSON
            try:
                plats = json.loads(profile.get("platforms") or "[]")
                profile["platform_list"] = plats or ["reddit", "hackernews"]
            except Exception:
                profile["platform_list"] = ["reddit", "hackernews"]
            return profile

    async def run_scan(self, search_profile_id: int, platform: str) -> dict:
        """Run a scan for a specific profile and platform."""
        from app.database import get_db_connection
        from app.utils.text_cleaner import clean_post
        from app.utils.dedup import DedupCache

        platform = str(platform).lower()
        scan_job: dict = {
            "status": ScanStatus.RUNNING,
            "platform": platform,
            "search_profile_id": search_profile_id,
            "leads_found": 0,
        }

        try:
            profile = await self._load_profile(search_profile_id)
            tags: list[str] = profile.get("tags", ["hiring"])
            min_budget = profile.get("min_budget") or profile.get("budget_min")
            location_pref = profile.get("location_pref") or profile.get("location")
            remote_only = bool(profile.get("remote_only", False))

            channel_cls = self.channels.get(platform)
            if not channel_cls:
                raise ValueError(f"Platform {platform} not supported")

            channel = channel_cls(self.settings, self.rate_limiter)
            raw_posts = await channel.fetch_posts(tags=tags)

            async with get_db_connection() as conn:
                for post in raw_posts:
                    try:
                        plat = str(post.get("platform", platform) or platform).lower()
                        ppid = str(post.get("platform_post_id") or uuid.uuid4())
                        title = post.get("title", "") or ""
                        body = post.get("body", "") or post.get("content_html", "") or post.get("content", "") or ""
                        cleaned = clean_post(title, body)

                        # Persist raw post first (SELECT-first to avoid lastrowid race on IGNORE)
                        cur0 = await conn.execute(
                            "SELECT id FROM raw_posts WHERE platform = ? AND platform_post_id = ?",
                            (plat, ppid),
                        )
                        existing = await cur0.fetchone()
                        if existing:
                            # Already processed this post; still check duplicate cache for safety
                            continue
                        if await DedupCache.is_duplicate(conn, plat, ppid):
                            continue
                        cur = await conn.execute(
                            """INSERT OR IGNORE INTO raw_posts
                               (platform, platform_post_id, title, content, body, author, url)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                plat,
                                ppid,
                                title,
                                cleaned,
                                body,
                                post.get("author", "Unknown") or "Unknown",
                                post.get("url", "") or "",
                            ),
                        )
                        if cur.rowcount == 0:
                            # Raced insert from concurrent scan; fetch winner and skip lead creation
                            cur2 = await conn.execute(
                                "SELECT id FROM raw_posts WHERE platform = ? AND platform_post_id = ?",
                                (plat, ppid),
                            )
                            r2 = await cur2.fetchone()
                            await conn.commit()
                            continue
                        raw_id = cur.lastrowid
                        await conn.commit()

                        # If no API key, use heuristic fallback so scans still produce leads locally
                        if not (getattr(self.settings, "openrouter_api_key", "") or "").strip():
                            text_l = (cleaned or "").lower()
                            has_intent = any(
                                k in text_l
                                for k in ["hiring", "looking for", "need a", "freelance", "contract", "help wanted", "job"]
                            )
                            tag_hit = [t for t in (tags or []) if t and t.lower() in text_l]
                            # tags is never empty (defaults applied in _load_profile), so require a tag hit
                            # unless caller explicitly passed empty tags list
                            if has_intent and (tag_hit or len(tags or []) == 0):
                                score = 0.85
                                await conn.execute(
                                    """INSERT INTO leads
                                       (raw_post_id, search_profile_id, profile_id, title, company, platform, url, author, author_name,
                                        content, tags, status, kanban_status, match_score, match_confidence, confidence_score)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', 'NEW', ?, ?, ?)""",
                                    (
                                        raw_id, search_profile_id, search_profile_id,
                                        title[:300], "", plat, post.get("url", ""),
                                        post.get("author", "Unknown"), post.get("author", "Unknown"),
                                        cleaned[:4000], json.dumps(tag_hit),
                                        score, score, round(score * 100, 1),
                                    ),
                                )
                                await conn.commit()
                                scan_job["leads_found"] += 1
                                logger.info(f"Heuristic lead for profile {search_profile_id} on {platform}")
                            continue

                        # AI path
                        intent_res = await self.intent_bouncer.classify(cleaned)
                        threshold = getattr(self.settings, "intent_confidence_threshold", 0.80)
                        if not self.intent_bouncer.is_passing(intent_res, threshold=threshold):
                            continue

                        match_res = await self.tag_matcher.match(
                            post_text=cleaned,
                            tags=tags,
                            min_budget=min_budget,
                            location_pref=location_pref,
                            remote_only=remote_only,
                        )
                        m_threshold = getattr(self.settings, "match_confidence_threshold", 0.85)
                        # Allow PARTIAL_MATCH with high confidence too
                        passing = self.tag_matcher.is_passing(match_res, threshold=m_threshold) or (
                            getattr(match_res.match_level, "value", "") == "PARTIAL_MATCH"
                            and match_res.confidence >= 0.70
                        )
                        if passing:
                            ext = match_res.extracted
                            await conn.execute(
                                """INSERT INTO leads
                                   (raw_post_id, search_profile_id, profile_id, title, company, platform, url, author, author_name,
                                    content, tags, status, kanban_status, match_score, match_confidence, confidence_score)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', 'NEW', ?, ?, ?)""",
                                (
                                    raw_id, search_profile_id, search_profile_id,
                                    (ext.title if ext and ext.title else title)[:300],
                                    (ext.company if ext and ext.company else "")[:200],
                                    plat, post.get("url", ""),
                                    post.get("author", "Unknown"), post.get("author", "Unknown"),
                                    cleaned[:4000], json.dumps(match_res.matched_tags),
                                    match_res.confidence, match_res.confidence,
                                    round(match_res.confidence * 100, 1),
                                ),
                            )
                            await conn.commit()
                            scan_job["leads_found"] += 1
                            logger.info(f"Lead found for profile {search_profile_id} on {platform}")
                    except Exception as e:
                        logger.error(f"Post processing failed: {e}")
                        continue

            scan_job["status"] = ScanStatus.COMPLETED

            # Update latest running scan_job row (case-insensitive for legacy lowercase rows)
            try:
                async with get_db_connection() as conn2:
                    await conn2.execute(
                        """UPDATE scan_jobs SET status='COMPLETED', completed_at=CURRENT_TIMESTAMP,
                           leads_found=?, items_found=? WHERE search_profile_id=? AND platform=? AND UPPER(status)='RUNNING'""",
                        (scan_job["leads_found"], scan_job["leads_found"], search_profile_id, platform),
                    )
                    await conn2.commit()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Scan pipeline failed for profile {search_profile_id} on {platform}: {e}")
            scan_job["status"] = ScanStatus.FAILED
            # Persist FAILED so /scan/status never sticks on RUNNING forever
            try:
                async with get_db_connection() as conn2:
                    await conn2.execute(
                        """UPDATE scan_jobs SET status='FAILED', completed_at=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP WHERE search_profile_id=? AND platform=? AND UPPER(status)='RUNNING'""",
                        (search_profile_id, platform),
                    )
                    await conn2.commit()
            except Exception:
                pass

        # Normalize for JSON
        scan_job["status"] = scan_job["status"].value if hasattr(scan_job["status"], "value") else str(scan_job["status"])
        return scan_job

    async def run_full_scan(self, search_profile_id: int) -> List[dict]:
        """Run a full scan across all enabled platforms for a profile."""
        profile = await self._load_profile(search_profile_id)
        enabled_platforms = profile.get("platform_list", ["reddit", "hackernews"])

        sem = asyncio.Semaphore(getattr(self.settings, "max_concurrent_scrapes", 3))

        async def _run_with_sem(plat: str):
            async with sem:
                return await self.run_scan(search_profile_id, plat)

        tasks = [_run_with_sem(plat) for plat in enabled_platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = [r for r in results if isinstance(r, Exception)]
        for f in failures:
            logger.error(f"Platform scan failed for profile {search_profile_id}: {f}")
        return [res for res in results if not isinstance(res, Exception)]


def build_default_pipeline() -> ScanPipeline:
    return ScanPipeline()
