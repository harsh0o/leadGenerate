# API Reference

**Base URL**: `http://localhost:8000/api`
**Authentication**: None (Designed for local execution)

## 1. Health

### `GET /health`
Returns the status of the backend API and database connection.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.0.0"
}
```

## 2. Personas

### `GET /personas`
List all personas.

### `POST /personas`
Create a new persona.

**Request:**
```json
{
  "name": "Full Stack Dev",
  "description": "Looking for contract work in React and Python.",
  "tags": ["react", "python", "fastapi", "contract", "freelance"]
}
```

## 3. Leads

### `GET /leads`
List leads, filterable by `persona_id` and `status`.

### `PATCH /leads/{id}/status`
Update lead status (e.g., moving on Kanban board).

**Request:**
```json
{
  "status": "Outreach"
}
```

## 4. Scans

### `POST /scan/start`
Trigger a manual scan on a specific platform.

**Request:**
```json
{
  "platform": "reddit",
  "persona_id": 1
}
```

### `GET /scan/live` (SSE endpoint)
Server-Sent Events for live radar updates.

**Event Types:**
- `scan_started`: `{ "platform": "reddit" }`
- `item_found`: `{ "title": "...", "url": "..." }`
- `ai_filtering`: `{ "status": "processing", "item_id": "..." }`
- `lead_qualified`: `{ "lead": { ... } }`

## 5. Drafts

### `POST /leads/{id}/draft`
Trigger the AI Auto-Drafter for a specific lead.

**Response:**
```json
{
  "draft_id": 12,
  "content": "Hi there, saw your post about needing a React dev...",
  "status": "ready"
}
```

## Error Format
All errors return a standard JSON structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Persona ID must be an integer.",
    "details": {}
  }
}
```
