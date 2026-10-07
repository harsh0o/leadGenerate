# Architecture Document

## System Overview

LeadHunter AI uses a modular architecture combining scraping components, an AI-powered filtering pipeline, and a local management dashboard.

```mermaid
flowchart TD
    subgraph Frontend
        Next[Next.js App Router]
        Tailwind[Tailwind CSS + Framer]
    end

    subgraph Backend
        FastAPI[FastAPI]
        Scheduler[APScheduler]
        DB[(SQLite)]
    end

    subgraph Channels
        Reddit[Reddit API]
        HN[HackerNews API]
        LI[LinkedIn Playwright]
        Twitter[RSSHub Twitter]
    end

    subgraph AI_Pipeline
        Bouncer[AI Bouncer (Llama-3)]
        Matcher[Tag Matcher]
        Drafter[AI Drafter]
    end

    Next <--> |REST & SSE| FastAPI
    Scheduler --> |Triggers| Channels
    Channels --> |Raw Data| Bouncer
    Bouncer --> |Filtered| Matcher
    Matcher --> |Qualified| FastAPI
    FastAPI <--> DB
    FastAPI <--> |Prompts| Drafter
```

## Dual-Agent AI Pipeline

The system uses a highly optimized dual-agent pattern to reduce hallucinations and ensure precision.
1. **AI Bouncer (Pass 1)**: Analyzes raw scraped posts to determine if they contain "intent to hire/buy". Returns a boolean and confidence score. This uses a very strict, low-temperature prompt.
2. **Tag Matcher (Pass 2)**: Only processes posts that passed the bouncer. Compares the post context against the Persona's tags (e.g., `react`, `python`). If a match is found, creates a rich structured JSON object representing the Lead.

## Database Schema

We use SQLite with 10 core tables:

1. `users` (id, username, created_at)
2. `personas` (id, user_id, name, description, active)
3. `persona_tags` (id, persona_id, tag_name, weight)
4. `channels` (id, platform, config_json, is_active)
5. `leads` (id, persona_id, source_id, title, url, status, intent_score)
6. `lead_tags` (id, lead_id, tag_id, match_score)
7. `drafts` (id, lead_id, content, created_at, status)
8. `scan_logs` (id, channel_id, started_at, ended_at, items_found, status)
9. `rate_limits` (id, platform, request_count, reset_time)
10. `settings` (id, key, value)

## Data Flow

1. **Scraper**: Pulls latest data via configured Channels.
2. **AI Bouncer**: Evaluates raw text. Drops noise.
3. **Tag Matcher**: Associates relevant Persona tags.
4. **Pydantic**: Validates the AI output schema (ensuring strict typing).
5. **DB**: Persists the qualified Lead.

## Channel Plugin Pattern

Inspired by Agent-Reach BaseChannel, all platforms inherit from a base class ensuring consistent interfaces for `scan()`, `fetch()`, and `authenticate()`.

## Stealth Fingerprinting 3-Layer System

To avoid detection on strict platforms (e.g., LinkedIn):
1. **Network**: Rotating User-Agents and localized timezone masking.
2. **Behavioral**: Humanized jitter (random wait times), scroll mimicking.
3. **Session**: Persisted browser contexts with persistent cookies via Playwright.

## Rate Limit Strategy per Platform

- Reddit: 1 req/sec. Tracked globally.
- HN: Unlimited (public API).
- LinkedIn: Strict limits per day to avoid account ban.
- X/Twitter: RSSHub handles rate limiting internally based on the host IP.

## Multi-Persona System Design

| Component | Function |
|-----------|----------|
| **Persona Engine** | Allows running multiple separate "identities" (e.g., SEO agency vs Full-stack dev). |
| **Routing** | Leads are routed to the specific Persona dashboard based on matching tags. |
| **Drafting context** | AI uses the Persona's description as context when drafting outreach. |
