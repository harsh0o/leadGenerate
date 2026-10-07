import asyncio
from loguru import logger

_scheduler = None


def setup_scheduler(app):
    """Setup APScheduler for background jobs."""
    global _scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.config import get_settings

        settings = get_settings()
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(
            scan_all_active_profiles,
            "interval",
            hours=max(1, settings.scan_interval_hours),
            id="scan_all_active_profiles",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        _scheduler.add_job(
            platform_health_check,
            "interval",
            minutes=30,
            id="platform_health_check",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,
        )
        _scheduler.add_job(
            cleanup_old_raw_posts,
            "cron",
            hour=3,
            id="cleanup_old_raw_posts",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        _scheduler.add_job(
            refresh_openrouter_models,
            "interval",
            hours=24,
            id="refresh_openrouter_models",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        _scheduler.start()
        logger.info("APScheduler started")
    except Exception as e:
        logger.warning(f"Scheduler not started: {e}")
    return _scheduler


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None


async def scan_all_active_profiles():
    """Queries active profiles, runs pipeline.run_full_scan for each."""
    logger.info("Running scan_all_active_profiles")
    try:
        from app.database import get_db_connection
        from app.scheduler.pipeline import build_default_pipeline

        async with get_db_connection() as conn:
            cur = await conn.execute("SELECT id FROM search_profiles WHERE is_active = 1")
            rows = await cur.fetchall()
            ids = [r["id"] for r in rows]
        if not ids:
            return
        pipeline = build_default_pipeline()
        for pid in ids:
            try:
                await pipeline.run_full_scan(pid)
            except Exception as e:
                logger.error(f"Full scan failed for {pid}: {e}")
    except Exception as e:
        logger.error(f"scan_all_active_profiles failed: {e}")


async def platform_health_check():
    """Iterates channels, calls health_check(), updates platform_health table."""
    logger.info("Running platform_health_check")
    try:
        from app.database import get_db_connection
        from app.config import get_settings
        from app.utils.rate_limiter import RateLimiter
        from app import channels as channels_pkg

        from app.utils.rate_limiter import get_shared_limiter
        settings = get_settings()
        rl = get_shared_limiter()
        mapping = {
            "reddit": channels_pkg.RedditChannel,
            "hackernews": channels_pkg.HackerNewsChannel,
            "linkedin": channels_pkg.LinkedInChannel,
            "twitter": channels_pkg.TwitterChannel,
            "threads": channels_pkg.ThreadsChannel,
        }
        async with get_db_connection() as conn:
            for name, cls in mapping.items():
                try:
                    ch = cls(settings, rl)
                    res = await ch.health_check()
                    if isinstance(res, tuple):
                        status = res[0].value if hasattr(res[0], "value") else str(res[0])
                        detail = res[1]
                    else:
                        status = str(res)
                        detail = None
                    cur = await conn.execute(
                        "UPDATE platform_health SET status=?, last_check_at=CURRENT_TIMESTAMP, last_check=CURRENT_TIMESTAMP, error_detail=?, consecutive_failures=CASE WHEN ?= 'HEALTHY' THEN 0 ELSE COALESCE(consecutive_failures,0)+1 END WHERE platform=?",
                        (status, detail, status, name),
                    )
                    if cur.rowcount == 0:
                        await conn.execute(
                            "INSERT INTO platform_health (platform, status, last_check_at, last_check, error_detail, consecutive_failures) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)",
                            (name, status, detail, 0 if status == "HEALTHY" else 1),
                        )
                    await conn.commit()
                except Exception as e:
                    try:
                        await conn.execute(
                            "UPDATE platform_health SET status='DOWN', last_check_at=CURRENT_TIMESTAMP, last_check=CURRENT_TIMESTAMP, error_detail=?, consecutive_failures=COALESCE(consecutive_failures,0)+1 WHERE platform=?",
                            (str(e)[:500], name),
                        )
                        await conn.commit()
                    except Exception:
                        pass
    except Exception as e:
        logger.error(f"platform_health_check failed: {e}")


async def cleanup_old_raw_posts():
    """DELETE FROM raw_posts WHERE created_at < (now - 30 days) AND id NOT IN (SELECT raw_post_id FROM leads)."""
    logger.info("Running cleanup_old_raw_posts")
    try:
        from app.database import get_db_connection

        async with get_db_connection() as conn:
            await conn.execute(
                """DELETE FROM raw_posts
                   WHERE datetime(created_at) < datetime('now', '-30 days')
                   AND id NOT IN (SELECT raw_post_id FROM leads WHERE raw_post_id IS NOT NULL)"""
            )
            await conn.commit()
    except Exception as e:
        logger.error(f"cleanup failed: {e}")


async def refresh_openrouter_models():
    """Fetch free models (logs only)."""
    logger.info("Running refresh_openrouter_models")
    try:
        from app.config import get_settings
        from app.ai.openrouter_client import OpenRouterClient

        s = get_settings()
        if not s.openrouter_api_key:
            return
        c = OpenRouterClient(api_key=s.openrouter_api_key, base_url=s.openrouter_base_url, model=s.openrouter_model)
        models = await c.get_available_free_models()
        logger.info(f"Found {len(models)} free models")
    except Exception as e:
        logger.error(f"refresh models failed: {e}")
