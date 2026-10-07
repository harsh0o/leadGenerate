# Setup Guide

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (Optional, but highly recommended for RSSHub)

## Step 1: Clone the Repository

```bash
git clone https://github.com/harsh0o/leadhunter-ai.git
cd leadhunter-ai
```

## Step 2: Backend Setup

```bash
cd backend
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```
Edit `backend/.env` and add your **OpenRouter API Key**. Set `DATABASE_URL=sqlite:///./leadhunter.db` (paths resolve against `backend/` dir).

## Step 3: Frontend Setup

```bash
cd ../frontend
npm install

# Configure environment variables
cp .env.local.example .env.local
```
Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000` (no `/api` suffix – routes already include `/api/*`; trailing `/api` would cause `/api/api/*` 404s).

## Step 4: RSSHub Setup (For X/Twitter)

If you plan to scan X/Twitter, you need RSSHub.

```bash
cd ../rsshub
cp .env.example .env
# Add your TWITTER_AUTH_TOKEN to the .env file
# Ensure REDIS_URL=redis://redis:6379/ is set (required when CACHE_TYPE=redis)
```

> Do NOT run the standalone `rsshub/docker-compose.yml` at the same time as the root
> `docker-compose.yml` – both bind port `1200`. Use the root compose (includes rsshub+redis):
> `docker compose up -d` from the repo root.
Verify it's running at `http://localhost:1200`.

## Step 5: LinkedIn Browser Profile Setup

For LinkedIn, we use a persistent Playwright context. You must log in manually once to save the session.

```bash
cd ../backend
python scripts/linkedin_login.py
```
A browser will open. Log into LinkedIn, wait for the feed to load, and close the browser. The session is now saved in `backend/linkedin_chrome_profile/` (matches `LINKEDIN_PROFILE_DIR` in `backend/.env`).

## Step 6: Start Services

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate # or venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:3000`.

## Troubleshooting

- **Database Errors**: Ensure the `DATABASE_URL` is correct and the directory is writable. You can run `python scripts/init_db.py` to create missing tables/indexes (it never drops data – it uses `CREATE TABLE IF NOT EXISTS`).
- **Playwright Errors**: Run `playwright install chromium` inside the backend virtual environment.
- **OpenRouter Rate Limits**: If using the free tier, ensure you aren't scanning too many items concurrently.
