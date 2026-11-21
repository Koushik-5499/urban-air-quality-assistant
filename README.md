# Urban Air Quality Assistant

An intelligent, full-stack urban air quality monitoring and health advisory platform.

## Architecture Overview

```text
urban-air-quality-assistant/
├── frontend/             # React 18 + TypeScript + Vite + Tailwind CSS + Recharts + Leaflet
│   └── src/
│       ├── services/api/ # Unified FastAPI Integration Layer
│       │   ├── client.ts       # Typed fetch wrapper with timeout & cancellation
│       │   ├── airQualityApi.ts# Live CPCB observations, NAQI calculations, stations
│       │   ├── historyApi.ts   # Historical records, trends, summaries & comparisons
│       │   ├── healthApi.ts    # AI Health Advisor & medical precautions
│       │   ├── alertsApi.ts    # Alerts feed, mutations & notification preferences
│       │   ├── forecastApi.ts  # Multi-horizon ML AQI predictions & model audit
│       │   ├── endpoints.ts    # 39 FastAPI v1 routes registry
│       │   ├── errors.ts       # Normalized ApiError mapping
│       │   └── types.ts        # TypeScript schemas matching backend Pydantic models
│       ├── context/      # LocationContext with race-condition prevention & live sync
│       └── pages/        # Dashboard, Pollutants, Analytics, Assistant, Alerts, Map, Locations
└── backend/              # Python 3.11+ + FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL
    └── app/
        ├── api/v1/       # 39 REST endpoints across 7 core environmental domains
        ├── core/         # Config, security, CORS, structured logging
        ├── db/           # Normalized database models & Alembic migrations
        └── services/     # CPCB NAQI Engine, AI Advisor, Forecaster, Alerting
```

## Quick Start

### 1. Backend Service
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Application
```bash
cd frontend
npm install
npm run dev
```
Access the application at: [http://localhost:5173](http://localhost:5173)

### 3. Environment Variables
Frontend (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT_MS=10000
VITE_APP_ENV=development
```

Backend (`backend/.env`):
```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./air_quality.db
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
AQI_PROVIDER=mock
GEMINI_API_KEY=your_gemini_api_key
```

## Verification & Testing
- **Frontend test suite**: `cd frontend && npm test` (43 passing tests across services, components, and API integration)
- **Frontend lint & build**: `cd frontend && npm run lint && npm run build` (Clean zero warnings)
- **Backend test suite**: `cd backend && pytest` (143 passing unit and integration tests)
