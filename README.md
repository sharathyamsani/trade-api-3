# Trade Opportunities API

A **FastAPI** service that analyzes market data and provides AI-powered trade opportunity insights for specific sectors in India.

---

## Features

| Feature | Details |
|---|---|
| **AI Analysis** | Google Gemini 1.5 Flash generates structured markdown reports |
| **Web Search** | DuckDuckGo scraping (free) or Serper.dev API (optional, richer results) |
| **Authentication** | JWT bearer tokens (guest tokens auto-issued) |
| **Rate Limiting** | Sliding-window per session/IP (default: 10 req / 60 s) |
| **Caching** | In-memory response cache keyed by sector + session |
| **Input Validation** | Pydantic models + custom sector name validation |
| **Auto Docs** | Swagger UI at `/docs`, ReDoc at `/redoc` |

---

## Quick Start

### 1. Clone / Extract

```bash
unzip trade_opportunities_api.zip
cd trade_opportunities_api
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a **free** Gemini API key at: https://aistudio.google.com/app/apikey

### 4. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** to explore the API interactively.

---

## API Reference

### `GET /`
Health check.

### `POST /auth/token`
Issue a guest JWT token.
```json
// Response
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "session_id": "uuid"
}
```

### `GET /analyze/{sector}` ⭐ Main Endpoint
Analyze trade opportunities for a sector.

**Path parameter:** `sector` – e.g., `pharmaceuticals`, `technology`, `agriculture`

**Query parameter:** `force_refresh=true` – bypass the cache

**Auth:** Include the JWT as a Bearer token header *(optional – guests are auto-created)*
```
Authorization: Bearer eyJ...
```

**Sample request:**
```bash
curl http://localhost:8000/analyze/pharmaceuticals
```

**Response:**
```json
{
  "sector": "pharmaceuticals",
  "report": "# Trade Opportunities Report: Pharmaceuticals...",
  "metadata": {
    "generated_at": 1712345678.0,
    "sources_used": ["https://..."],
    "analysis_model": "gemini-1.5-flash",
    "sector_normalized": "pharmaceuticals"
  },
  "cached": false
}
```

### `GET /sectors`
List of well-known supported sectors.

### `GET /session/info`
Usage stats for the current session.

---

## Architecture

```
trade_opportunities_api/
├── main.py            # FastAPI app, routes, middleware, dependencies
├── config.py          # Environment-based settings (pydantic-settings)
├── models.py          # Pydantic request/response models
├── auth.py            # JWT creation & verification
├── rate_limiter.py    # Sliding-window in-memory rate limiter
├── data_collector.py  # Web search (Serper / DuckDuckGo)
├── analyzer.py        # Gemini AI integration + fallback report
├── requirements.txt
├── .env.example
└── README.md
```

### Request Flow

```
Client
  └─► GET /analyze/{sector}
        ├─ JWT auth (auto-guest if missing)
        ├─ Rate limit check (10 req/60 s per session+IP)
        ├─ Input validation (length, allowed chars)
        ├─ Cache check → return cached if hit
        ├─ DataCollector: parallel web searches (4 queries)
        ├─ TradeAnalyzer: Gemini API call with structured prompt
        ├─ Cache store
        └─► AnalysisResponse (markdown report + metadata)
```

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `SERPER_API_KEY` | *(blank)* | Serper.dev key (optional) |
| `JWT_SECRET_KEY` | *(change me!)* | Secret for JWT signing |
| `JWT_EXPIRE_MINUTES` | `1440` | Token lifetime in minutes |
| `RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `RATE_LIMIT_WINDOW` | `60` | Window size in seconds |
| `CACHE_TTL_SECONDS` | `3600` | Cache lifetime (informational) |

---

## Running Without a Gemini Key

The API runs in **demo mode** without `GEMINI_API_KEY`. It still collects real web search data but generates a template-based report. Add the key in `.env` to enable full AI analysis.

---

## Example Report Structure

The generated markdown report includes:

1. Executive Summary
2. Current Market Overview
3. Export Opportunities
4. Import Dynamics
5. Government Policies & Incentives (PLI, FDI, Trade Agreements)
6. Key Trends & Drivers
7. Challenges & Risks
8. Investment Opportunities
9. Key Trade Partners (with data table)
10. Recommendations

---

## Security Notes

- **JWT tokens** expire after 24 h by default.
- **Rate limiting** is per `session_id:IP` to prevent abuse.
- **Input sanitisation** rejects sectors with special characters.
- Change `JWT_SECRET_KEY` to a cryptographically random value in production.
- Add HTTPS (TLS) termination via nginx or a cloud load balancer before going live.

---

## License

MIT – free to use and modify.
