# Vercel Deployment & Production Operations Guide

**Project:** Urban Air Quality Assistant  
**Repository:** [https://github.com/Koushik-5499/urban-air-quality-assistant](https://github.com/Koushik-5499/urban-air-quality-assistant)  
**Date:** November 21, 2026  
**Status:** Vercel Configuration Ready  

---

## 1. Architecture Overview

The Urban Air Quality Assistant is structured for deployment across two independent Vercel projects linked to the same GitHub repository:

```text
GitHub: Koushik-5499/urban-air-quality-assistant
  ├── Project 1: Frontend (Root: /frontend) -> Vite SPA (HTML/JS/CSS on Edge CDN)
  └── Project 2: Backend (Root: /backend)   -> FastAPI Serverless Functions (/api/index.py)
```

---

## 2. Project 1: Frontend (Vite + React)

### 2.1 Project Settings in Vercel Dashboard
- **Project Name:** `urban-air-quality-frontend` (or user-chosen name)
- **Framework Preset:** `Vite`
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### 2.2 Environment Variables (Frontend)
Configure these under **Project Settings > Environment Variables**:

| Variable Name | Environment | Recommended Value | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Production | `https://your-backend.vercel.app` | Backend FastAPI deployment URL (WITHOUT trailing `/api/v1` as the client appends it). |
| `VITE_API_BASE_URL` | Preview | `https://your-backend-preview.vercel.app` | Preview deployment backend URL. |
| `VITE_API_TIMEOUT_MS` | All | `10000` | HTTP request timeout in milliseconds. |
| `VITE_APP_ENV` | Production / Preview | `production` / `staging` | Runtime environment flag. |

> [!WARNING]
> **Zero Secrets Policy:** Never place Gemini API keys, admin secrets, or database credentials in `VITE_*` environment variables. All client-side environment variables are publicly visible in the compiled browser bundle.

### 2.3 Single-Page Application (SPA) Routing
A [frontend/vercel.json](file:///data/urban-air-quality-assistant/frontend/vercel.json) configuration has been placed to route all client-side navigation paths (`/analytics`, `/pollutants`, `/map`, `/assistant`, `/alerts`, `/locations`) to `/index.html`:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 3. Project 2: Backend (FastAPI / Python Serverless)

### 3.1 Project Settings in Vercel Dashboard
- **Project Name:** `urban-air-quality-backend`
- **Framework Preset:** `Other` (Python Serverless)
- **Root Directory:** `backend`
- **Build Command:** *(Leave default / blank)*
- **Output Directory:** *(Leave default / blank)*
- **Install Command:** `pip install -r requirements.txt`

### 3.2 Serverless Function Entry Point
The backend uses [backend/api/index.py](file:///data/urban-air-quality-assistant/backend/api/index.py) to export the FastAPI `app` instance. All incoming requests are routed through [backend/vercel.json](file:///data/urban-air-quality-assistant/backend/vercel.json):

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/api/index.py"
    }
  ]
}
```

### 3.3 Environment Variables (Backend)
Configure these securely in **Project Settings > Environment Variables** (marked as Sensitive):

#### Application Core
- `APP_ENV`: `production` (disables interactive `/docs` and enforces strict security headers/CORS)
- `APP_VERSION`: `1.0.0`
- `API_V1_PREFIX`: `/api/v1`
- `LOG_LEVEL`: `INFO`
- `CORS_ORIGINS`: `["https://your-frontend.vercel.app"]` (Specify explicit frontend origin; no wildcard `*` in production)

#### Database
- `DATABASE_URL`: Connection string to persistent PostgreSQL/managed database (e.g. `postgresql://user:pass@host/dbname?sslmode=require`).
  > [!IMPORTANT]
  > **Ephemeral Storage Limitation:** Vercel serverless functions do not provide persistent local filesystem storage. Local SQLite (`air_quality.db`) is read-only or wiped across invocations. For production persistence, use a hosted database (such as Neon Serverless Postgres or Supabase).

#### External Providers (CPCB & Weather)
- `AQI_PROVIDER`: `cpcb` (or `mock` for dry-run/preview)
- `CPCB_API_BASE_URL`: `https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69`
- `CPCB_API_KEY`: *(Optional key from data.gov.in dashboard)*
- `AQI_FETCH_TIMEOUT`: `10.0`
- `AQI_CACHE_TTL_SECONDS`: `300`
- `AQI_MAX_RETRIES`: `2`
- `WEATHER_PROVIDER`: `open-meteo`
- `WEATHER_API_BASE_URL`: `https://api.open-meteo.com/v1`
- `WEATHER_ENABLED`: `true`

#### Gemini AI Health Advisor
- `GEMINI_API_KEY`: *(Google AI Studio / Gemini API key)*
- `GEMINI_MODEL`: `gemini-2.5-flash`
- `AI_PROVIDER`: `gemini`
- `AI_ENABLED`: `true`
- `AI_REQUEST_TIMEOUT`: `30`
- `AI_MAX_RETRIES`: `2`

#### Administrative Secrets (Secure Ingestion & Forecasting)
Generate high-entropy random keys for administrative routes:
```bash
openssl rand -hex 32
```
- `SYNC_ADMIN_SECRET`: Secret key protecting `POST /api/v1/air-quality/sync`
- `ALERT_ADMIN_SECRET`: Secret key protecting `POST /api/v1/alerts/trigger-check`
- `FORECAST_ADMIN_SECRET`: Secret key protecting `POST /api/v1/forecast/generate`
- `ADMIN_SECRET_KEY`: Central master administrative secret checked by `verify_admin_access`

#### Browser Push Notifications
- `WEB_PUSH_ENABLED`: `true`
- `VAPID_PUBLIC_KEY`: *(Application VAPID public key)*
- `VAPID_PRIVATE_KEY`: *(Application VAPID private key)*
- `VAPID_SUBJECT`: `mailto:admin@your-domain.com`
- `EMAIL_NOTIFICATIONS_ENABLED`: `false` (Strictly disabled)

---

## 4. Deployment Sequence

1. **Deploy Backend Project First:**
   - Deploy `urban-air-quality-backend` with Root Directory = `backend`.
   - Verify health endpoint: `GET https://your-backend.vercel.app/health/ready`.
   - Verify API versioning: `GET https://your-backend.vercel.app/health/live`.
2. **Deploy Frontend Project Second:**
   - Set `VITE_API_BASE_URL` to the verified backend URL.
   - Deploy `urban-air-quality-frontend` with Root Directory = `frontend`.
   - Verify dashboard loads and connects to live backend.
3. **Configure Cross-Origin Resource Sharing (CORS):**
   - Update backend's `CORS_ORIGINS` environment variable to include the newly assigned frontend URL:
     ```json
     ["https://your-frontend.vercel.app"]
     ```
   - Trigger a redeployment of the backend so the updated CORS whitelist takes effect.
