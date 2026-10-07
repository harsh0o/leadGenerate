# Platform Integration & Scraping Guide

This document details how LeadHunter interacts with various platforms, current limitations, and risk assessments.

## 1. Reddit

- **Method**: Direct `.json` endpoints (e.g., `https://reddit.com/r/forhire/new.json`).
- **User-Agent**: Reddit strictly requires unique User-Agents. We use a format like: `desktop:leadhunter:v1.0 (by /u/yourusername)`.
- **Rate Limits**: Strictly 1 request per second. Violating this will result in an IP ban.
- **Target Subreddits**:
  - `r/forhire`
  - `r/hiring`
  - `r/freelance`
  - `r/cofounder`

## 2. HackerNews

- **Method**: Firebase Public API and Algolia Search API.
- **Approach**: We specifically monitor the monthly "Who is hiring?" and "Freelancer? Seeking freelancer?" threads.
- **Rate Limits**: Extremely generous. We use asynchronous fetching to process threads quickly.

## 3. LinkedIn

- **Method**: Headless browser automation via Playwright using a persistent context.
- **Mechanism**: We do not scrape HTML. We intercept Voyager API network requests (JSON responses) while mimicking human scrolling.
- **Limits**:
  - Max 50 profile views per day.
  - Max 30-40 search queries per day.
- **Risks**: High. Requires a seasoned/warmed-up account. Use at your own risk.

## 4. X (Twitter)

- **Method**: Self-hosted RSSHub translating X queries into RSS feeds.
- **Auth**: Requires `TWITTER_AUTH_TOKEN` from browser cookies.
- **Approach**: We use specific search query routes in RSSHub, e.g., `/twitter/keyword/"looking for a react developer"`.
- **Limits**: Handled by X based on the account providing the auth token. Avoid more than 100 queries an hour.

## 5. Threads

- **Method**: RSSHub route.
- **Future Path**: Meta is releasing an official API which will eventually replace the RSSHub integration for more reliable querying.

## Risk Assessment Table

| Platform | Difficulty | Ban Risk | Reliability | Data Richness |
|----------|------------|----------|-------------|---------------|
| Reddit | Low | Low | High | Medium |
| HackerNews| Low | None | Very High | High |
| LinkedIn | High | High | Low | Very High |
| X/Twitter| Medium | Medium | Medium | Low |
| Threads | Medium | Low | Medium | Low |
