"""Force recreate DB schema. Usage: python scripts/init_db.py"""
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.database import init_db


async def main():
    await init_db()
    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(main())
