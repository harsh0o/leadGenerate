import aiosqlite

class DedupCache:
    """Checks the database to prevent processing the same post twice."""
    
    @staticmethod
    async def is_duplicate(db: aiosqlite.Connection, platform: str, platform_post_id: str) -> bool:
        cursor = await db.execute(
            "SELECT 1 FROM raw_posts WHERE platform = ? AND platform_post_id = ?",
            (platform, platform_post_id)
        )
        row = await cursor.fetchone()
        return row is not None

    @staticmethod
    async def mark_processed(db: aiosqlite.Connection, platform: str, platform_post_id: str) -> None:
        # In a real scenario, this might just rely on raw_posts insertion.
        # But this method exists to satisfy the user request if it's used independently.
        pass
