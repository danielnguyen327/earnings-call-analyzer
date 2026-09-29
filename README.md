# CallScope

AI-powered earnings call analysis. Enter a ticker and quarter, and CallScope fetches the real earnings call transcript, splits it into prepared remarks / Q&A / closing, and uses Claude to generate structured sentiment, management confidence, key themes, forward guidance, and risk factors — with a sentiment wave, quarter-over-quarter comparison, and searchable history.

## Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, Vite, Tailwind CSS
- **Data**: [Equibles](https://equibles.com/) for earnings call transcripts, Nasdaq's public symbol directory for company search (no key needed)
- **AI**: [Claude](https://www.anthropic.com/) (Anthropic) for structured analysis

## Setup

### Option A — Docker Compose (recommended)

1. Create `backend/.env` (see [Environment variables](#environment-variables) below) — only `EQUIBLES_API_KEY` and `ANTHROPIC_API_KEY` are needed; `DATABASE_URL` is overridden by Compose.
2. From the project root:
   ```bash
   docker compose up --build
   ```
3. Backend is now running at `http://localhost:8000`.
4. In a separate terminal, run the frontend (Compose doesn't bundle it yet):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. Open `http://localhost:5173`.

### Option B — Manual (local Postgres + venv)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create `backend/.env` (see below), pointing `DATABASE_URL` at your own local Postgres instance. Then:
```bash
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Environment variables

Set these in `backend/.env`:

| Variable | Description |
|---|---|
| `EQUIBLES_API_KEY` | Get a free key at [equibles.com](https://equibles.com/). Free tier allows **100 requests/day**; a transcript fetch uses one (two for calls with over 200 speaker turns). |
| `ANTHROPIC_API_KEY` | Get a key at [console.anthropic.com](https://console.anthropic.com/). |
| `DATABASE_URL` | e.g. `postgresql://postgres:postgres@localhost:5432/earnings_analyzer`. Ignored under Docker Compose (auto-set to point at the `db` service). |
| `APP_ENV` | `development` (or anything — informational only). |

## Running tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Tests use an in-memory SQLite database and mock all external services (Equibles, Nasdaq's symbol directory, Claude) — no real network calls or API quota consumed. Note: `app.main` connects to the real `DATABASE_URL` at import time to create tables, so a reachable Postgres instance is still required to run the suite (CI spins up a throwaway one automatically).

## API overview

| Endpoint | Description |
|---|---|
| `POST /calls/{ticker}/{quarter}/fetch` | Fetch and cache a transcript |
| `POST /calls/{ticker}/{quarter}/analyze` | Run Claude analysis on a cached transcript |
| `GET /calls/{ticker}/{quarter}` | Retrieve a cached transcript |
| `GET /analyses/{ticker}/{quarter}` | Retrieve a stored analysis |
| `GET /analyses?ticker=` | List analyses for one ticker (or all tickers if omitted) |
| `GET /analyses/recent` | Most recently analyzed ticker+quarter per ticker |
| `DELETE /analyses?ticker=` | Clear analysis history (all, or one ticker) |
| `GET /companies/search?q=` | Company name → ticker lookup from Nasdaq's symbol directory, for autocomplete |

All fetch/analyze endpoints are deduplicated: an already-fetched transcript or already-run analysis is served from Postgres instead of re-calling the external API.

## Known limitations

- Quarters follow each company's **fiscal** calendar, as Equibles reports them — e.g. NVIDIA's May 2026 call is `2027Q1`.
- Equibles' free tier allows **100 requests/day**. Already-fetched tickers/quarters don't count against it, since they're served from the database.
- Company search covers US-listed stocks (Nasdaq, NYSE and other US exchanges) and refreshes daily. ETFs, warrants, units and preferred shares are left out.
