"""Manual LinkedIn login to persist Playwright session.
Usage: python scripts/linkedin_login.py
Opens a browser, user logs into LinkedIn, session saved to profile dir.
"""
import asyncio
from app.config import get_settings


async def main():
    from playwright.async_api import async_playwright

    settings = get_settings()
    profile_dir = getattr(settings, "linkedin_profile_dir", "./linkedin_chrome_profile")
    print(f"Using profile dir: {profile_dir}")
    print("A browser will open. Log into LinkedIn, wait for feed, then close browser.")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
        )
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login", wait_until="networkidle")
        print("Waiting 120s for manual login...")
        try:
            await page.wait_for_url("**/feed/**", timeout=120000)
            print("Login detected. Session saved.")
        except Exception:
            print("Timeout. Close browser manually; session may still be saved.")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
