# Urban Air Quality Assistant — Frontend

React 18 + TypeScript + Vite frontend client connected to the FastAPI environmental backend.

## Key Features & Backend Integrations

- **Live CPCB NAQI Engine**: Connected to `GET /api/v1/aqi/calculate` and `GET /api/v1/air-quality/cities/{city_name}`. Displays real-time NAQI index, dominant pollutants, breakpoint categories, and sub-indices.
- **Race Condition Prevention**: `LocationContext` utilizes `AbortController` cancellation to ensure rapid city switching never suffers from stale async overwrites.
- **Atmospheric Pollutant Analysis**: Real-time sensor metrics for PM2.5, PM10, CO, NO2, SO2, and O3, with WHO and CPCB standard limits.
- **Historical Analytics & Comparisons**: Connected to `/api/v1/history/aqi`, `/summary`, `/trends`, and `/compare` to evaluate pollution trajectories and compare Indian metros.
- **AI Health Advisor**: Connected to `POST /api/v1/health/ask` powered by Google Gemini, offering medical precautions, mask advisories, and outdoor exercise safety with graceful fallback.
- **Alerts & Notification Preferences**: Connected to `/api/v1/alerts`, `/unread-count`, `/read-all`, and `/preferences`.
- **Air Quality Forecasting**: Connected to `/api/v1/forecast/aqi`, `/hourly`, and `/daily` displaying predicted AQI and confidence bounds.
- **Geospatial Map & Locations**: Connected to `/api/v1/stations` and `/api/v1/air-quality/cities` displaying active station telemetry and coverage.

## Environment Variables

Configured via `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT_MS=10000
VITE_APP_ENV=development
```

## Available Scripts

- `npm run dev`: Start Vite development server
- `npm run build`: Type-check with `tsc -b` and produce optimized production build
- `npm run lint`: Run ESLint checks
- `npm test`: Run Vitest integration and unit test suite
