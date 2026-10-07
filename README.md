# LeadHunter AI

> 100% Free, Local-First AI Lead Generation Agent

Created by: [harsh0o](https://github.com/harsh0o)

LeadHunter AI is an open-source, local-first platform designed to automate lead generation across multiple platforms using dual-agent AI pipelines. Hunt leads precisely based on persona tags, automatically draft outreach messages, and manage your pipeline through a built-in Kanban CRM.

## ✨ Features

- **Multi-Persona Profiles**: Set up different offerings or identities and hunt leads relevant to each.
- **Tag-Based Criteria**: Filter opportunities aggressively with AI-driven tag matching to ignore the noise.
- **Live Radar**: Watch the AI scan platforms in real-time with server-sent events.
- **Kanban CRM**: Track leads visually from Discovery -> Qualify -> Outreach -> Negotiate -> Won/Lost.
- **AI Auto-Drafter**: Instantly generate hyper-personalized outreach drafts tailored to each prospect based on scraped context.
- **100% Free AI**: Utilizes OpenRouter's free tier for AI analysis—no API costs.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11+), Pydantic v2, SQLite, APScheduler, httpx
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion
- **AI Engine**: OpenRouter API (free models), Dual-agent LLM pipeline
- **Scraping Infrastructure**: Playwright, RSSHub, Native APIs

## 🚀 Quick Start Guide

### Docker Method (Recommended)
The easiest way to get started is by using Docker Compose.

```bash
# Clone the repository
git clone https://github.com/harsh0o/leadhunter-ai.git
cd leadhunter-ai

# Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
cp rsshub/.env.example rsshub/.env

# Add your OpenRouter API key to backend/.env
# Add your TWITTER_AUTH_TOKEN to rsshub/.env (if scanning X/Twitter)

# Start all services
docker-compose up -d
```
Access the application at `http://localhost:3000`.

### Manual Method
For development or running without Docker, see the [Detailed Setup Guide](docs/SETUP.md).

## 📸 Screenshots
*(Coming soon)*
- Dashboard overview
- Multi-persona creation
- Live radar scanning
- Kanban board
- Auto-drafting in action

## 🏗 Architecture Overview

LeadHunter uses a modular plugin architecture for scraping channels, feeding raw data into an AI Bouncer (first-pass filter) and then a Tag Matcher (second-pass semantic filter). Verified leads are passed through Pydantic validators into a local SQLite database.

For a detailed dive, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Please check the issues page and feel free to submit a pull request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
