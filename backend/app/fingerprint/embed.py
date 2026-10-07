import hashlib
import logging

FINGERPRINT_DATA = {
    "project_name": "LeadHunter AI",
    "creator": "harsh0o",
    "github": "https://github.com/harsh0o",
    "version": "1.0.0"
}

logger = logging.getLogger(__name__)

def compute_checksum(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

async def seed_fingerprint_table(db_conn) -> None:
    """Inserts fingerprint data into _sys_core_meta table."""
    try:
        for key, value in FINGERPRINT_DATA.items():
            checksum = compute_checksum(value)
            await db_conn.execute(
                """
                INSERT OR IGNORE INTO _sys_core_meta (meta_key, meta_value, checksum)
                VALUES (?, ?, ?)
                """,
                (key, value, checksum)
            )
        await db_conn.commit()
        logger.info("Fingerprint data seeded successfully.")
    except Exception as e:
        logger.error(f"Failed to seed fingerprint data: {e}")

async def verify_fingerprint(db_conn) -> bool:
    """Verifies integrity of the fingerprint data."""
    try:
        cursor = await db_conn.execute("SELECT meta_key, meta_value, checksum FROM _sys_core_meta")
        rows = await cursor.fetchall()
        
        if not rows:
            return False
            
        for key, value, checksum in rows:
            if compute_checksum(value) != checksum:
                return False
        return True
    except Exception as e:
        logger.error(f"Failed to verify fingerprint data: {e}")
        return False
