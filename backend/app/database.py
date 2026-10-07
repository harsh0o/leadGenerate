import aiosqlite
import logging
import pathlib
from contextlib import asynccontextmanager
from app.config import get_settings
from app.fingerprint.embed import seed_fingerprint_table

logger = logging.getLogger(__name__)


def _resolve_db_path(database_url: str) -> str:
    # Supports sqlite:///./leadhunter.db , sqlite:///absolute, sqlite:///:memory:
    # Also supports plain filesystem paths (including Windows C:\\...).
    if database_url == "sqlite:///:memory:" or database_url == ":memory:":
        return ":memory:"
    if database_url.startswith("sqlite:///"):
        p = database_url.replace("sqlite:///", "", 1)
        # sqlite:////tmp/x.db -> /tmp/x.db ; sqlite:///./x.db -> ./x.db
        if p.startswith("/") and not p.startswith("//") and len(p) > 1 and p[1] == ":":
            p = p[1:]
        if p.startswith("//"):
            p = p[1:]
        return p
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "", 1)
    return database_url


def get_db_path() -> str:
    settings = get_settings()
    raw = _resolve_db_path(settings.database_url)
    if raw != ":memory:" and not pathlib.Path(raw).is_absolute():
        # Resolve relative DB paths against backend/ dir, not process CWD
        base = pathlib.Path(__file__).resolve().parent.parent
        return str(base / raw)
    return raw


@asynccontextmanager
async def get_db_connection():
    db_path = get_db_path()
    # Ensure parent dir exists for file DBs
    if db_path != ":memory:":
        parent = pathlib.Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path, timeout=30.0)
    conn.row_factory = aiosqlite.Row
    try:
        try:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=30000")
            await conn.execute("PRAGMA foreign_keys=ON")
            await conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass
        yield conn
    finally:
        await conn.close()


async def init_db():
    """Initializes the database schema (superset supporting all API routes)."""
    async with get_db_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona TEXT NOT NULL DEFAULT 'FREELANCER',
                display_name TEXT DEFAULT 'Admin',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                location_pref TEXT,
                location TEXT,
                remote_only BOOLEAN DEFAULT 0,
                min_budget REAL,
                budget_min REAL,
                budget_max REAL,
                currency TEXT DEFAULT 'USD',
                platforms TEXT DEFAULT '["reddit","hackernews"]',
                is_active BOOLEAN DEFAULT 1,
                last_scan_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS profile_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_profile_id INTEGER NOT NULL,
                profile_id INTEGER,
                tag TEXT NOT NULL,
                tag_type TEXT NOT NULL DEFAULT 'KEYWORD',
                FOREIGN KEY (search_profile_id) REFERENCES search_profiles(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_profile_id INTEGER,
                profile_id INTEGER,
                platform TEXT NOT NULL DEFAULT 'reddit',
                platforms TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING',
                leads_found INTEGER DEFAULT 0,
                items_found INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS raw_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_post_id TEXT NOT NULL,
                title TEXT,
                content TEXT,
                body TEXT,
                author TEXT,
                url TEXT,
                posted_at TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_raw_platform_post UNIQUE(platform, platform_post_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_post_id INTEGER,
                search_profile_id INTEGER,
                profile_id INTEGER,
                title TEXT DEFAULT '',
                company TEXT DEFAULT '',
                platform TEXT DEFAULT 'reddit',
                url TEXT DEFAULT '',
                author TEXT DEFAULT '',
                author_name TEXT DEFAULT '',
                content TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'NEW',
                kanban_status TEXT DEFAULT 'NEW',
                match_score REAL DEFAULT 0,
                match_confidence REAL DEFAULT 0,
                confidence_score REAL DEFAULT 0,
                priority INTEGER DEFAULT 3,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS lead_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                draft_type TEXT NOT NULL DEFAULT 'COLD_DM',
                type TEXT DEFAULT 'COLD_DM',
                content TEXT NOT NULL,
                tone TEXT DEFAULT 'PROFESSIONAL',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS _sys_core_meta (
                meta_key TEXT PRIMARY KEY,
                meta_value TEXT NOT NULL,
                checksum TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS platform_health (
                platform TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'HEALTHY',
                last_check_at TIMESTAMP,
                last_check TIMESTAMP,
                error_detail TEXT,
                consecutive_failures INTEGER DEFAULT 0
            )
        """)

        # Performance / integrity indexes (idempotent)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_profile ON leads(search_profile_id, profile_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_platform ON leads(platform)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_profile ON scan_jobs(search_profile_id, profile_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_raw_posts_lookup ON raw_posts(platform, platform_post_id)")
        # Enforce composite uniqueness (platform, platform_post_id) for pre-existing DBs
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_platform_post ON raw_posts(platform, platform_post_id)"
        )

        await db.commit()

        # Migrate legacy raw_posts schema where platform_post_id was globally UNIQUE
        # (same id on different platforms would collide and silently drop leads).
        try:
            cur = await db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='raw_posts'"
            )
            row = await cur.fetchone()
            ddl = (row[0] if row and row[0] else "") or ""
            if "platform_post_id TEXT NOT NULL UNIQUE" in ddl.replace("  ", " "):
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS raw_posts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        platform_post_id TEXT NOT NULL,
                        title TEXT,
                        content TEXT,
                        body TEXT,
                        author TEXT,
                        url TEXT,
                        posted_at TIMESTAMP,
                        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_raw_platform_post UNIQUE(platform, platform_post_id)
                    )
                """)
                # Copy, keeping first row per (platform, platform_post_id)
                await db.execute("""
                    INSERT OR IGNORE INTO raw_posts_new
                        (id, platform, platform_post_id, title, content, body, author, url, posted_at, scraped_at, created_at)
                    SELECT id, platform, platform_post_id, title, content, body, author, url, posted_at, scraped_at, created_at
                    FROM raw_posts ORDER BY id
                """)
                await db.execute("DROP TABLE raw_posts")
                await db.execute("ALTER TABLE raw_posts_new RENAME TO raw_posts")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_raw_posts_lookup ON raw_posts(platform, platform_post_id)")
                await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_platform_post ON raw_posts(platform, platform_post_id)")
                await db.commit()
                logger.info("Migrated raw_posts to composite UNIQUE(platform, platform_post_id)")
        except Exception as e:
            logger.warning(f"raw_posts migration skipped: {e}")

        # Seed default user
        cur = await db.execute("SELECT id FROM users WHERE id = 1")
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO users (id, display_name, persona) VALUES (1, 'Admin', 'FREELANCER')"
            )
            await db.commit()

        # Seed platform health rows
        for plat in ["reddit", "hackernews", "linkedin", "twitter", "threads"]:
            await db.execute(
                "INSERT OR IGNORE INTO platform_health (platform, status) VALUES (?, 'HEALTHY')",
                (plat,),
            )
        await db.commit()

        await seed_fingerprint_table(db)
        logger.info("Database initialized successfully.")
