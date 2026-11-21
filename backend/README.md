# Urban Air Quality Assistant — Backend API

FastAPI-powered asynchronous backend service for the Urban Air Quality Assistant platform. Provides real-time environmental monitoring endpoints, external air quality data ingestion from the official Government of India CPCB portal, a deterministic CPCB National Air Quality Index (NAQI) processing engine, health check services, structured logging, robust CORS integration, and a normalized SQLAlchemy 2.0 database architecture with Alembic migrations.

---

## 1. Technology Stack

- **Python**: 3.11+ (Python 3.14 compatible)
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/) (>= 0.115.0)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) with `uvloop` & `httptools`
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Mapped columns, 2.0-style statements)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/) (>= 1.14.0)
- **Database Engine**: SQLite (default local development) / PostgreSQL ready
- **External Integration & HTTP Client**: [HTTPX](https://www.python-httpx.org/) (Asynchronous with connection pooling & bounded retries)
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) and `pydantic-settings`
- **Email Delivery**: [Resend](https://resend.com/) API via HTTPX
- **Web Push Notifications**: `pywebpush` with VAPID signing
- **Environment Management**: `python-dotenv`
- **Testing**: `pytest`, `pytest-asyncio`, `anyio`, and `httpx`

---

## 2. Directory Structure

```text
backend/
├── alembic/                      # Alembic migration environment
│   ├── env.py                    # Migration runner configured with app models & settings
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Versioned migration scripts
│       └── bc2db0976544_create_initial_models.py
├── app/
│   ├── __init__.py               # Package marker & metadata
│   ├── main.py                   # FastAPI application factory, middleware & root endpoints
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py         # Master router assembling all v1 route modules
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py     # GET /api/v1/health & AI Advisor endpoints
│   │           ├── air_quality.py# Air quality observations, availability, diagnostics & sync
│   │           ├── aqi.py        # CPCB NAQI calculation, latest, history, and processing
│   │           ├── history.py    # Historical AQI trends, comparisons & aggregations
│   │           ├── alerts.py     # Air quality alerts, notifications, preferences & push
│   │           ├── forecast.py   # Future AQI forecasts, hourly, daily & model evaluation
│   │           └── stations.py   # Monitoring stations query endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic Settings & environment variable validation
│   │   └── logging.py            # Centralized structured logging setup
│   ├── db/
│   │   ├── __init__.py           # Database package entrypoint
│   │   ├── base.py               # DeclarativeBase & unified model registration
│   │   ├── session.py            # Engine, sessionmaker, and get_db dependency
│   │   ├── init_db.py            # Database health probe & diagnostics
│   │   └── seed.py               # Repeatable city seed command (python -m app.db.seed)
│   ├── integrations/             # External provider integration layer
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAQIProvider interface & NormalizedObservation schema
│   │   ├── cpcb/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # Asynchronous HTTP client with bounded retries & backoff
│   │   │   ├── mapper.py         # CPCB record parser, unit & IST->UTC timestamp normalizer
│   │   │   ├── provider.py       # CPCB implementation of BaseAQIProvider
│   │   │   └── exceptions.py     # CPCB-specific exceptions (auth, timeout, rate limit, parse)
│   │   ├── weather/              # Meteorological data integration layer
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # Asynchronous Open-Meteo client with caching & retries
│   │   │   └── schemas.py        # Weather observation & status models
│   │   └── mock/
│   │       ├── __init__.py
│   │       └── provider.py       # Simulated provider for offline testing & development
│   ├── models/
│   │   ├── __init__.py           # SQLAlchemy models exports
│   │   ├── city.py               # Indian Cities entity (coordinates, state, unique constraint)
│   │   ├── monitoring_station.py # Environmental monitoring stations
│   │   ├── pollutant_reading.py  # Pollutant concentration readings (PM2.5, PM10, etc.)
│   │   ├── aqi_reading.py        # Composite AQI readings (simulated & observed)
│   │   ├── alert.py              # Air quality alerts & warnings
│   │   ├── alert_preference.py   # User threshold & notification preferences
│   │   ├── push_subscription.py  # Browser Web Push credentials (VAPID)
│   │   └── forecast.py           # ForecastRun, AQIForecast, and ForecastEvaluation entities
│   ├── schemas/
│   │   ├── __init__.py           # Pydantic schemas exports
│   │   ├── common.py             # Reusable API response and error models
│   │   ├── health.py             # Health and root response validation models
│   │   ├── city.py               # City request/response schemas
│   │   ├── monitoring_station.py # Station request/response schemas
│   │   ├── pollutant.py          # Pollutant reading schemas
│   │   ├── aqi.py                # Base AQI reading schemas
│   │   ├── aqi_processing.py     # Phase 4 NAQI calculation, sub-indices & history schemas
│   │   ├── alert.py              # Alert schemas
│   │   ├── forecast.py           # Hourly, daily, history & model evaluation schemas
│   │   └── air_quality.py        # Real-time air quality, availability & sync schemas
│   ├── repositories/
│   │   ├── __init__.py           # Repository exports
│   │   ├── city_repository.py    # City CRUD operations
│   │   ├── station_repository.py # Station queries & creation
│   │   └── reading_repository.py # Pollutant readings, AQI readings & alert queries
│   └── services/
│       ├── __init__.py           # Services exports
│       ├── aqi_data_service.py   # Ingestion orchestrator, caching, freshness & deduplication
│       ├── data_normalization_service.py # Canonical city & pollutant matching rules
│       ├── aqi/                  # CPCB NAQI Processing Engine
│       │   ├── __init__.py
│       │   ├── breakpoints.py    # Official CPCB breakpoint tables for 8 pollutants
│       │   ├── calculator.py     # Deterministic linear interpolation & worst-pollutant rule
│       │   ├── categories.py     # Official categories, ranges, and color codes
│       │   ├── dominant_pollutant.py # Dominant pollutant identification & tie-breaking
│       │   ├── processor.py      # Batch processor, station grouping & deduplicated persistence
│       │   └── validators.py     # Concentration, unit, and CPCB data sufficiency validation
│       ├── alerts/               # Phase 7 Alerts & Notification System
│       │   ├── __init__.py
│       │   ├── threshold_engine.py   # Condition detection & NAQI severity mapping
│       │   ├── deduplication.py      # Deterministic key generation & active window suppression
│       │   ├── delivery_tracker.py   # Timezone-aware quiet hours & critical override
│       │   ├── notification_service.py # Resend email, Web Push (VAPID) & templates
│       │   ├── alert_generator.py    # Alert record creation & DB persistence
│       │   └── alert_service.py      # Orchestrator for evaluation, listing & management
│       └── forecasting/          # Phase 8 Air Quality Forecasting System
│           ├── __init__.py
│           ├── validators.py         # Horizon and sample count constraints
│           ├── data_preparation.py   # Chronological dataset extraction & splitting
│           ├── feature_engineering.py # Lags, rolling averages, and diurnal cyclical encodings
│           ├── confidence.py         # Residual standard error & prediction intervals
│           ├── evaluation.py         # Out-of-sample MAE, RMSE, MAPE & baseline comparisons
│           ├── forecast_service.py   # End-to-end forecasting orchestrator
│           └── models/               # Statistical and ML time-series models
│               ├── __init__.py
│               ├── base.py           # BaseForecastModel contract
│               ├── persistence.py    # Persistence baseline (Last-Value)
│               ├── moving_average.py # Rolling window baseline
│               ├── exponential_smoothing.py # Holt-Winters with damped trend & 24h diurnal cycle
│               └── factory.py        # Model instantiation factory
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared test fixtures & isolated in-memory test DB
│   ├── test_health.py            # Root, health, CORS, and security tests
│   ├── test_database.py          # Models, constraints, foreign keys, repos & seed tests
│   ├── test_air_quality.py       # CPCB client, mapping, retries, deduplication, caching & API tests
│   ├── test_aqi_engine.py        # NAQI breakpoints, sub-indices, tie-breakers, sufficiency & API tests
│   ├── test_history.py           # Historical trends, aggregations & comparisons tests
│   ├── test_ai_advisor.py        # Gemini AI advisor, fallback & safety tests
│   ├── test_alerts.py            # Alert detection, deduplication, quiet hours & API tests
│   └── test_forecast.py          # Time-series models, horizons, evaluation & forecast API tests
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Python, venv, and cache ignore rules
├── alembic.ini                   # Alembic configuration file
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Production and test dependencies
└── README.md                     # Backend service documentation
```

---

## 3. Official CPCB NAQI Calculation Methodology

The backend implements the official **Indian National Air Quality Index (NAQI)** calculation standard established by the **Central Pollution Control Board (CPCB)**, Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India.

*Note: This methodology strictly uses the Indian CPCB standard and does not substitute US EPA formulas.*

### 1. Mathematical Formula

For a given pollutant concentration $C_p$, the sub-index $I_p$ is calculated by linear interpolation between its lower breakpoint ($B_{low}$) and upper breakpoint ($B_{high}$):

$$I_p = I_{low} + \frac{I_{high} - I_{low}}{B_{high} - B_{low}} \times (C_p - B_{low})$$

Where:
- $C_p$: Measured pollutant concentration.
- $B_{low}, B_{high}$: Breakpoint concentration bounds corresponding to $C_p$.
- $I_{low}, I_{high}$: AQI sub-index bounds corresponding to the category interval.
- $I_p$: Resulting pollutant sub-index rounded to the nearest integer ($0 \le I_p \le 500$).

### 2. Official CPCB Breakpoint Table

| Category | AQI Range | $\text{PM}_{2.5}$ *(24-hr)* | $\text{PM}_{10}$ *(24-hr)* | $\text{NO}_2$ *(24-hr)* | $\text{SO}_2$ *(24-hr)* | $\text{CO}$ *(8-hr)* | $\text{O}_3$ *(8-hr)* | $\text{NH}_3$ *(24-hr)* | $\text{Pb}$ *(24-hr)* |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Units** | | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ | $\text{mg/m}^3$ | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **Good** | **0–50** | 0–30 | 0–50 | 0–40 | 0–40 | 0.0–1.0 | 0–50 | 0–200 | 0.0–0.5 |
| **Satisfactory** | **51–100** | 31–60 | 51–100 | 41–80 | 41–80 | 1.1–2.0 | 51–100 | 201–400 | 0.5–1.0 |
| **Moderately Polluted** | **101–200** | 61–90 | 101–250 | 81–180 | 81–380 | 2.1–10.0 | 101–168 | 401–800 | 1.1–2.0 |
| **Poor** | **201–300** | 91–120 | 251–350 | 181–280 | 381–800 | 10.1–17.0 | 169–208 | 801–1200 | 2.1–3.0 |
| **Very Poor** | **301–400** | 121–250 | 351–430 | 281–400 | 801–1600 | 17.1–34.0 | 209–748 | 1201–1800 | 3.1–3.5 |
| **Severe** | **401–500** | 250+ | 430+ | 400+ | 1600+ | 34.0+ | 748+ | 1800+ | 3.5+ |

### 3. Data Quality & Minimum Sufficiency Rules
Under official CPCB NAQI guidelines, an **Overall Composite AQI** can only be officially declared when:
1. **At least three criteria pollutants** are monitored ($N \ge 3$).
2. **At least one particulate matter pollutant** ($\text{PM}_{2.5}$ or $\text{PM}_{10}$) is mandatory.

*If these criteria are not met, the engine returns the individual pollutant sub-indices, but refuses to guess or invent a composite numerical AQI (`aqi: null`, `data_quality: "insufficient_data"`).*

### 4. Dominant Pollutant Resolution & Tie-Breaking
The dominant pollutant is the pollutant with the maximum sub-index:
$$\text{AQI} = \max(I_1, I_2, \dots, I_n)$$
When two or more pollutants share the exact same maximum sub-index, ties are resolved deterministically using a health-impact priority hierarchy:
$$\text{PM}_{2.5} > \text{PM}_{10} > \text{NO}_2 > \text{O}_3 > \text{CO} > \text{SO}_2 > \text{NH}_3 > \text{Pb}$$

### 5. Why Hourly Telemetry Is Labeled "1-hour (indicative)"
Regulatory CPCB NAQI breakpoints are calibrated for 24-hour averages ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{NH}_3$, $\text{Pb}$) and 8-hour rolling averages ($\text{CO}$, $\text{O}_3$). Real-time provider data streams hourly snapshots. The engine clearly reports these calculations with `averaging_period: "1-hour (indicative)"` and avoids falsely claiming an instantaneous hourly measurement is an official 24-hour regulatory average.

---

## 4. Worked Calculation Example

### Input Observations:
- $\text{PM}_{2.5} = 38.5\ \mu\text{g/m}^3$
- $\text{PM}_{10} = 72.0\ \mu\text{g/m}^3$
- $\text{NO}_2 = 24.1\ \mu\text{g/m}^3$
- $\text{SO}_2 = 11.3\ \mu\text{g/m}^3$
- $\text{CO} = 0.85\ \text{mg/m}^3$
- $\text{O}_3 = 28.0\ \mu\text{g/m}^3$

### Calculated Sub-Indices:
1. **$\text{PM}_{2.5}$ ($38.5\ \mu\text{g/m}^3$)**:
   Falls in Satisfactory interval ($30–60\ \mu\text{g/m}^3 \to 51–100$):
   $$I_{\text{PM}_{2.5}} = 51 + \frac{100 - 51}{60 - 30} \times (38.5 - 30) = 51 + \frac{49}{30} \times 8.5 \approx 64.88 \to \mathbf{65}\ (\text{Satisfactory})$$
2. **$\text{PM}_{10}$ ($72.0\ \mu\text{g/m}^3$)**:
   Falls in Satisfactory interval ($50–100\ \mu\text{g/m}^3 \to 51–100$):
   $$I_{\text{PM}_{10}} = 51 + \frac{100 - 51}{100 - 50} \times (72.0 - 50) = 51 + \frac{49}{50} \times 22 \approx 72.56 \to \mathbf{73}\ (\text{Satisfactory})$$
3. **$\text{NO}_2$ ($24.1\ \mu\text{g/m}^3$)**:
   Falls in Good interval ($0–40\ \mu\text{g/m}^3 \to 0–50$):
   $$I_{\text{NO}_2} = 0 + \frac{50 - 0}{40 - 0} \times (24.1 - 0) \approx 30.13 \to \mathbf{30}\ (\text{Good})$$
4. **$\text{SO}_2$ ($11.3\ \mu\text{g/m}^3$)**:
   Falls in Good interval ($0–40\ \mu\text{g/m}^3 \to 0–50$):
   $$I_{\text{SO}_2} = 0 + \frac{50}{40} \times 11.3 \approx 14.13 \to \mathbf{14}\ (\text{Good})$$
5. **$\text{CO}$ ($0.85\ \text{mg/m}^3$)**:
   Falls in Good interval ($0–1.0\ \text{mg/m}^3 \to 0–50$):
   $$I_{\text{CO}} = 0 + \frac{50}{1.0} \times 0.85 = \mathbf{42}\ (\text{Good})$$
6. **$\text{O}_3$ ($28.0\ \mu\text{g/m}^3$)**:
   Falls in Good interval ($0–50\ \mu\text{g/m}^3 \to 0–50$):
   $$I_{\text{O}_3} = 0 + \frac{50}{50} \times 28.0 = \mathbf{28}\ (\text{Good})$$

### Synthesis:
- **Maximum Sub-Index**: $\max(65, 73, 30, 14, 42, 28) = \mathbf{73}$
- **Dominant Pollutant**: $\mathbf{\text{PM}_{10}}$
- **Overall NAQI**: $\mathbf{73}$
- **Category**: **Satisfactory**
- **Data Sufficiency**: **Sufficient** (6 pollutants present including $\text{PM}_{2.5}$ and $\text{PM}_{10}$)

---

## 5. API Endpoints

### 1. `GET /api/v1/aqi/calculate`
Calculates NAQI sub-indices and overall index on the fly for a specified city or monitoring station.
- Query parameters: `city` (optional), `station_id` (optional).
- Returns: `AQICalculationResponse` with sub-indices for every available pollutant, overall index, dominant pollutant, and data sufficiency status.

### 2. `GET /api/v1/aqi/pollutant-subindices`
Returns only individual pollutant sub-indices and dominant driver pollutant without overall AQI packaging.
- Query parameters: `city` (optional), `station_id` (optional).

### 3. `GET /api/v1/aqi/latest`
Retrieves the most recent persisted `AQIReading` record from the database.
- Query parameters: `city` (optional), `station_id` (optional).
- Returns `HTTP 404` with a clean message if no record has been processed yet.

### 4. `GET /api/v1/aqi/history`
Retrieves paginated historical calculated AQI records.
- Query parameters: `city`, `station_id`, `start_date`, `end_date`, `page` (default 1), `page_size` (default 50).
- Returns: `AQIHistoryResponse`.

### 5. `POST /api/v1/aqi/process`
Batch processor that evaluates current stored pollutant measurements, calculates NAQI, and persists deduplicated records to `aqi_readings`.
- Query parameters: `city_id` (optional).

---

## 6. Running Migrations, Seeding & Tests

```bash
cd backend
source .venv/bin/activate

# 1. Run migrations
alembic upgrade head

# 2. Seed 10 supported Indian cities
python -m app.db.seed

# 3. Run all 90 automated tests
pytest -v

# 4. Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 7. Phase 5: Historical Data Service

### 7.1 Historical Data Architecture
The Historical Data Service provides scalable, temporally consistent, and verifiable access to longitudinal air quality records. It leverages normalized database records:
- **`AQIReading` (`aqi_readings`)**: Stores historical composite NAQI calculations, category classifications, dominant pollutants, source attribution, simulation flags, and data quality indicators.
- **`PollutantReading` (`pollutant_readings`)**: Stores discrete pollutant concentrations, units, measurement timestamps in UTC, simulation flags, and data quality ratings.
- **Optimized Indexes**:
  - `ix_aqi_city_measured`: `(city_id, measured_at)`
  - `ix_aqi_station_measured`: `(station_id, measured_at)`
  - `ix_pollutant_city_code_measured`: `(city_id, pollutant_code, measured_at)`
  - `ix_pollutant_station_code_measured`: `(station_id, pollutant_code, measured_at)`
  - Single-column indexes on `is_simulated`, `measured_at`, `city_id`, `station_id`, and `pollutant_code`.

### 7.2 Aggregation Rules & Conventions
- **Timezone Policy**: All timestamps are stored, indexed, and aggregated in **Coordinated Universal Time (UTC)**.
- **Daily Aggregation**: Grouped by UTC calendar day (`YYYY-MM-DD 00:00:00+00:00` to `23:59:59.999999+00:00`).
- **Weekly Aggregation**: Follows **ISO-8601 week convention** starting on **Monday at 00:00:00 UTC**.
- **Monthly Aggregation**: Follows calendar month boundaries starting on the **1st of the month at 00:00:00 UTC**.
- **Preservation of Missing Periods**: Intervals without valid telemetry are never filled with synthetic or interpolated numbers; missing periods are preserved as gaps.
- **Statistical Summaries**:
  - `min`, `max`, `average` (mean rounded to 1 decimal place for AQI, 2 decimal places for concentrations), and `median`.
  - Excludes records with invalid status or null values.
  - Aggregates valid composite AQI readings directly—does not average raw pollutant concentrations to create an artificial AQI.
  - For pollutant aggregates, reproducible CPCB NAQI sub-indices are calculated for the mean concentration.

### 7.3 Trend Analysis Methodology
The dual-horizon comparative trend engine evaluates whether environmental conditions are improving, deteriorating, or stable:
1. The requested time range is partitioned into two consecutive chronological halves: Earlier Period $[T_{start}, T_{mid})$ and Later Period $[T_{mid}, T_{end}]$.
2. Both periods require a configurable minimum number of valid observations (`min_records_per_period`, default `3`).
3. If either period lacks sufficient observations, the trend is classified as `"insufficient_data"`.
4. Movement is evaluated against a stability threshold ($\Delta = 5.0$ AQI points or $2.0\,\mu\text{g/m}^3$ for concentrations):
   - **Improving**: $\Delta < -\text{threshold}$ (AQI or concentration decreased, air quality improved).
   - **Worsening**: $\Delta > +\text{threshold}$ (AQI or concentration increased, air quality degraded).
   - **Stable**: $|\Delta| \le \text{threshold}$ (movement remains within stability boundary).

### 7.4 Historical API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/history/aqi` | Paginated AQI history with optional hourly, daily, weekly, or monthly aggregation. |
| `GET` | `/api/v1/history/pollutants` | Paginated pollutant concentrations with reproducible CPCB sub-indices and optional aggregation. |
| `GET` | `/api/v1/history/summary` | Summary statistics (min, max, mean, median, category and dominant pollutant distributions). |
| `GET` | `/api/v1/history/trends` | Trend analysis comparing earlier and later temporal halves. |
| `GET` | `/api/v1/history/compare` | Multi-city or multi-station comparison over identical date horizons (2 to 10 targets). |

---

### 7.5 Example API Requests and Responses

#### 1. Retrieve a City's Last 7 Days of AQI History (Daily Aggregation)
**Request:**
```http
GET /api/v1/history/aqi?city=Delhi&interval=daily&page=1&page_size=7 HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "page": 1,
  "page_size": 7,
  "total_records": 7,
  "total_pages": 1,
  "city": "Delhi",
  "station_id": null,
  "station_name": null,
  "interval": "daily",
  "period_start": null,
  "period_end": null,
  "records": [
    {
      "period_start": "2026-11-01T00:00:00Z",
      "period_end": "2026-11-02T00:00:00Z",
      "interval": "daily",
      "average_aqi": 150.0,
      "min_aqi": 150,
      "max_aqi": 150,
      "median_aqi": 150.0,
      "record_count": 1,
      "dominant_category": "Moderate",
      "category_distribution": {
        "Moderate": 1
      },
      "dominant_pollutant": "PM2.5",
      "source": "CPCB",
      "is_simulated": false,
      "data_quality": "valid",
      "city_name": "Delhi",
      "station_id": null,
      "station_name": null
    }
  ]
}
```

#### 2. Retrieve a Pollutant's Monthly History
**Request:**
```http
GET /api/v1/history/pollutants?city=Delhi&pollutant=PM2.5&interval=monthly HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "page": 1,
  "page_size": 20,
  "total_records": 1,
  "total_pages": 1,
  "city": "Delhi",
  "station_id": null,
  "station_name": null,
  "pollutant": "PM2.5",
  "unit": "µg/m³",
  "interval": "monthly",
  "period_start": null,
  "period_end": null,
  "records": [
    {
      "period_start": "2026-11-01T00:00:00Z",
      "period_end": "2026-12-01T00:00:00Z",
      "interval": "monthly",
      "pollutant_code": "PM2.5",
      "unit": "µg/m³",
      "average": 50.8,
      "minimum": 30.0,
      "maximum": 72.0,
      "median": 50.0,
      "sub_index": 85,
      "sub_index_category": "Satisfactory",
      "record_count": 10,
      "source": "CPCB",
      "is_simulated": true,
      "data_quality": "valid",
      "city_name": "Delhi",
      "station_id": null,
      "station_name": null
    }
  ]
}
```

#### 3. Retrieve Historical AQI Summary
**Request:**
```http
GET /api/v1/history/summary?city=Delhi HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "city": "Delhi",
  "station_id": null,
  "station_name": null,
  "period_start": "2026-11-01T10:00:00Z",
  "period_end": "2026-11-10T10:00:00Z",
  "min_aqi": 90,
  "max_aqi": 160,
  "average_aqi": 125.0,
  "median_aqi": 125.0,
  "record_count": 10,
  "category_distribution": {
    "Moderate": 6,
    "Satisfactory": 4
  },
  "dominant_pollutant_distribution": {
    "PM2.5": 10
  },
  "data_quality": "sufficient"
}
```

#### 4. Compare Air Quality Between Two Cities
**Request:**
```http
GET /api/v1/history/compare?cities=Delhi,Bengaluru HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "period_start": null,
  "period_end": null,
  "location_count": 2,
  "comparisons": [
    {
      "location_type": "city",
      "city_name": "Delhi",
      "station_id": null,
      "station_name": null,
      "average_aqi": 125.0,
      "min_aqi": 90,
      "max_aqi": 160,
      "median_aqi": 125.0,
      "record_count": 10,
      "category_distribution": {
        "Moderate": 6,
        "Satisfactory": 4
      },
      "dominant_pollutant_distribution": {
        "PM2.5": 10
      },
      "data_quality": "sufficient"
    },
    {
      "location_type": "city",
      "city_name": "Bengaluru",
      "station_id": null,
      "station_name": null,
      "average_aqi": 48.8,
      "min_aqi": 45,
      "max_aqi": 52,
      "median_aqi": 49.0,
      "record_count": 5,
      "category_distribution": {
        "Good": 4,
        "Satisfactory": 1
      },
      "dominant_pollutant_distribution": {
        "PM10": 5
      },
      "data_quality": "sufficient"
    }
  ]
}
```

---

## 8. Phase 6: AI Health Advisor

### 8.1 AI Architecture & Provider Integration
The AI Health Advisor provides context-grounded, educational public-health guidance based on live environmental observations.
- **Provider Abstraction (`app/integrations/ai/`)**:
  - `BaseAIProvider`: Abstract interface defining `generate_response()`, `is_configured()`, and telemetry metadata.
  - `GeminiProvider`: Production provider built with Google's official `google-genai` Python SDK, utilizing `gemini-2.5-flash` with asynchronous client execution, bounded exponential backoff retries, and strict request timeouts.
  - Safe error handling: Missing credentials, rate limits (HTTP 429), timeouts, and outages map to domain exceptions without exposing API keys or secrets in logs or API responses.

### 8.2 Gemini Setup & Configuration
To enable live AI completions:
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add your key to `backend/.env` (or set environment variables):
   ```bash
   GEMINI_API_KEY="your-gemini-api-key-here"
   GEMINI_MODEL="gemini-2.5-flash"
   AI_PROVIDER="gemini"
   AI_ENABLED=true
   AI_REQUEST_TIMEOUT=30
   AI_MAX_RETRIES=2
   ```
*(Note: If `GEMINI_API_KEY` is omitted, the application operates normally by automatically utilizing the deterministic public health knowledge-base fallback.)*

### 8.3 Supported AI Capabilities
1. **Context-Grounded Q&A (`POST /api/v1/health/ask`)**: Answers health inquiries (e.g., *"Is it safe to exercise outside today?"*, *"Should children play outdoors?"*) using live AQI observations for the selected city.
2. **Actionable Recommendations (`GET /api/v1/health/recommendations`)**: Categorized advice spanning outdoor exercise, commuting, indoor ventilation, vulnerable groups, and children.
3. **Official Guidelines (`GET /api/v1/health/guidelines`)**: CPCB and WHO guidance covering all 6 NAQI categories and sensitive target groups.
4. **Pollutant Explanations (`GET /api/v1/health/pollutants/{pollutant_code}`)**: Educational breakdowns for all 8 criteria pollutants (`PM2.5`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `NH3`, `Pb`).
5. **Operational Status (`GET /api/v1/health/status`)**: Reports AI provider readiness and model identifier without leaking secrets.

### 8.4 Health Knowledge-Base Sources
Guidance is strictly grounded in official scientific and regulatory publications:
- **Central Pollution Control Board (CPCB)**, MoEFCC, Govt of India — *National Air Quality Index (2014)*.
- **World Health Organization (WHO)** — *Global Air Quality Guidelines (2021)*.
- **Ministry of Health and Family Welfare (MoHFW)**, Govt of India — *Advisory on Air Pollution*.
- **Indian Council of Medical Research (ICMR)** — *Air Pollution Health Impact Assessment*.

### 8.5 Safety, Privacy & Guardrails
- **Non-Medical Disclaimer**: General guidance is explicitly labeled as educational and not a substitute for clinical medical advice.
- **Prescription & Diagnostic Filtering**: The advisor never diagnoses conditions, prescribes pharmaceuticals, or instructs users to stop prescribed treatments.
- **No Absolute Guarantees**: The engine clarifies that N95 masks and HEPA purifiers substantially reduce particulate exposure but do not guarantee complete protection.
- **Data Grounding**: Backend environmental telemetry is injected into prompts as factual data blocks. Missing or stale data (> 5 hours old) is explicitly acknowledged.
- **Privacy**: User inquiries and conversation history are bounded (maximum 10 turns, 500 characters per question). No personal medical profiles or credentials are logged or persisted.

### 8.6 Fallback Behaviour
When Gemini is unconfigured, disabled, or temporarily unavailable (rate limits, timeouts, network interruptions), the advisor automatically delivers structured guidance synthesized from the CPCB/WHO knowledge base. Responses are transparently flagged with:
```json
"response_type": "knowledge_base_fallback"
```

### 8.7 Example API Requests and Responses

#### 1. Ask Health Assistant
**Request:**
```http
POST /api/v1/health/ask HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "city": "Delhi",
  "question": "Is it safe to go for a run in Delhi this afternoon?"
}
```
**Response:**
```json
{
  "answer": "Based on verified air quality data for Delhi, the current AQI is 240 (Poor) with PM2.5 as the dominant pollutant. Outdoor running is not recommended. Heavy cardiovascular exertion increases your breathing rate and deposits high amounts of fine particulate matter deep into the lungs. Consider exercising indoors in a clean-air environment.\n\nDisclaimer: This guidance is provided for educational and environmental awareness purposes only. It does not constitute professional medical advice.",
  "recommendations": [
    {
      "title": "Substitute Outdoor Exercise with Indoor Alternatives",
      "description": "Avoid outdoor running and intense cardiovascular exercise. Exercise indoors in a well-ventilated space.",
      "target_group": "General adults",
      "priority": "high",
      "reason": "High respiration rates during outdoor exercise drastically increase deep-alveolar deposition of fine particulates.",
      "supporting_source": "CPCB NAQI (2014)"
    }
  ],
  "aqi_context": {
    "city_name": "Delhi",
    "station_id": 1,
    "station_name": "Anand Vihar CAAQMS",
    "aqi": 240,
    "category": "Poor",
    "dominant_pollutant": "PM2.5",
    "measurement_timestamp": "2026-11-20T14:00:00Z",
    "data_age_seconds": 1800,
    "is_stale": false,
    "is_simulated": false,
    "data_source": "CPCB",
    "trend_direction": "improving"
  },
  "sources": [
    "Central Pollution Control Board (CPCB) NAQI (2014)",
    "WHO Global Air Quality Guidelines (2021)"
  ],
  "disclaimer": "Disclaimer: This guidance is provided for educational and environmental awareness purposes only...",
  "data_freshness": "fresh",
  "response_type": "ai_generated",
  "model": "gemini-2.5-flash"
}
```

#### 2. Get AI Advisor Status
**Request:**
```http
GET /api/v1/health/status HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "ai_enabled": true,
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "available": false,
  "api_key_configured": false
}
```

---

## 9. Phase 7: Alerts & Notifications System

The Alerts & Notifications subsystem continuously evaluates environmental conditions across all configured cities and monitoring stations. When air pollution breaches safety levels or shifts rapidly, alerts are generated and dispatched through In-App, Email (via Resend), and Web Push (via VAPID/`pywebpush`) channels.

### 9.1 Detection Engine & Trigger Conditions
The engine detects six primary environmental events:
1. **Category Transitions (`CATEGORY_CHANGE`)**: Triggered when AQI moves into a worse category (e.g., *Moderate* to *Poor*), advising immediate precautions.
2. **Threshold Crossings (`THRESHOLD_CROSSING`)**: Triggered when AQI crosses standard (e.g., 100, 200, 300) or user-configured thresholds.
3. **Sudden Deterioration Spikes (`DETERIORATION`)**: Triggered when AQI worsens rapidly ($\ge 30$ points within the monitoring window), even within the same category.
4. **Significant Improvements (`IMPROVEMENT`)**: Triggered when AQI drops substantially ($\ge 40$ points) into a healthier category.
5. **Dominant Pollutant Shifts (`POLLUTANT_CHANGE`)**: Triggered when the primary pollution driver changes (e.g., PM2.5 to NO2) at elevated levels ($\ge 150$).
6. **Stale Data Warnings (`STALE_DATA`)**: Triggered when station telemetry has not updated for $> 24$ hours.

### 9.2 NAQI Severity Mapping
Alert severity maps directly to Indian CPCB NAQI categories:
| NAQI Category | AQI Range | Alert Severity | Action Guidance |
| :--- | :--- | :--- | :--- |
| **Good** | 0 – 50 | `Low` | Air quality is satisfactory; normal outdoor activities. |
| **Satisfactory** | 51 – 100 | `Low` | Minor breathing discomfort to sensitive people. |
| **Moderate** | 101 – 200 | `Moderate` | Breathing discomfort to people with asthma and heart diseases. |
| **Poor** | 201 – 300 | `High` | Breathing discomfort to most people on prolonged exposure. |
| **Very Poor** | 301 – 400 | `High` | Respiratory illness on prolonged exposure. |
| **Severe** | 401 – 500+ | `Critical` | Affects healthy people; serious impacts on existing conditions. |

### 9.3 Deduplication Strategy
To avoid alert fatigue:
- Each alert receives a deterministic deduplication key: `{city_id}:{station_id or 'city'}:{alert_type}:{current_aqi}:{YYYYMMDDHH}`.
- Active deduplication window: Alerts with identical keys or matching `(city_id, station_id, alert_type)` within a configurable 2-hour window are suppressed.
- Expired alerts do not block fresh alerts.

### 9.4 Quiet Hours & Life-Safety Overrides
- Users can define quiet hours (e.g. `22:00` to `07:00`) in their local IANA timezone (`Asia/Kolkata` by default).
- During quiet hours, routine notifications (`Low`, `Moderate`, `High`) are suppressed (`delivery_status="skipped_quiet_hours"`).
- **Life-Safety Critical Override**: `Critical` severity alerts (`Severe` AQI $\ge 401$) bypass quiet hours unconditionally to protect vulnerable populations.

### 9.5 Multi-Channel Notification Dispatch
- **In-App Alerts**: Always persisted to the `alerts` database table with `is_read=False`.
- **Email Dispatch**: Delivered via the official [Resend](https://resend.com) API using asynchronous HTTPX with authorization tokens, multipart HTML/plain-text templates, timeout protection, and retry bounds.
- **Web Push**: Standard Web Push over VAPID via `pywebpush`. Auto-prunes expired subscriptions returning HTTP `410 Gone` or `404 Not Found`.

### 9.6 Simulated Data Handling & Safety
When alert candidates are derived from simulated data:
- Titles are prefixed with `[SIMULATED DATA]`.
- Descriptions explicitly state: *"Simulated Data: This notification is based on simulated environmental modeling."*
- Alerts are marked with `is_simulated=True` and filtered separately from certified CPCB observations.

### 9.7 Alerts REST Endpoints (`/api/v1/alerts`)
| Method | Path | Summary | Protection |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/alerts` | Paginated alerts with filtering (`city`, `station_id`, `severity`, `is_read`, `is_simulated`, dates) | Public |
| `GET` | `/api/v1/alerts/unread-count` | Retrieve total count of unread alerts | Public |
| `PATCH` | `/api/v1/alerts/{alert_id}/read` | Mark specific alert as read (404 if not found) | Public |
| `PATCH` | `/api/v1/alerts/read-all` | Mark all unread alerts as read | Public |
| `GET` | `/api/v1/alerts/preferences` | Retrieve user notification and threshold preferences | Public (`X-User-Id`) |
| `PUT` | `/api/v1/alerts/preferences` | Update user notification channels, thresholds, quiet hours | Public (`X-User-Id`) |
| `POST` | `/api/v1/alerts/process` | Trigger bounded evaluation and notification dispatch run | Admin (`X-Admin-Secret`) |
| `GET` | `/api/v1/alerts/status` | Engine status, enabled channels, and provider readiness | Public |
| `POST` | `/api/v1/alerts/test-notification` | Dev test endpoint for email, push, or in-app delivery | Admin (`X-Admin-Secret`) |
| `POST` | `/api/v1/alerts/push/subscribe` | Register or update browser Web Push subscription | Public (`X-User-Id`) |

---

## 10. Phase 8: Air Quality Forecasting Service

The Air Quality Forecasting subsystem delivers predictive insights into future air quality conditions across multiple horizons (1 hour to 72 hours). It utilizes statistical time-series modeling with diurnal seasonal decomposition, empirical prediction intervals, out-of-sample performance evaluation against persistence baselines, and optional meteorological feature integration.

### 10.1 Forecasting Architecture
The service is structured modularly under [backend/app/services/forecasting/](file:///data/urban-air-quality-assistant/backend/app/services/forecasting/):
```text
backend/app/services/forecasting/
├── __init__.py                # Package exports
├── validators.py              # Horizon validation and dataset constraints
├── data_preparation.py        # Chronological extraction, deduplication, and leakage-free splitting
├── feature_engineering.py     # Lags, rolling window statistics, and diurnal cyclical features
├── confidence.py              # Calibrated prediction intervals and horizon uncertainty expansion
├── evaluation.py              # Out-of-sample MAE, RMSE, MAPE, and baseline comparisons
├── forecast_service.py        # End-to-end forecasting orchestrator
└── models/                    # Model family implementations
    ├── base.py                # BaseForecastModel contract
    ├── persistence.py         # Persistence baseline (Last-Value)
    ├── moving_average.py      # Rolling window moving average
    ├── exponential_smoothing.py # Holt-Winters with damped trend & 24h diurnal cycle
    └── factory.py             # Model instantiation factory
```

### 10.2 Forecasting Methodology
1. **Holt-Winters Exponential Smoothing with Damped Trend**:
   - Level equation: $L_t = \alpha (y_t - S_{t-m}) + (1-\alpha)(L_{t-1} + \phi T_{t-1})$
   - Trend equation: $T_t = \beta (L_t - L_{t-1}) + (1-\beta)\phi T_{t-1}$
   - Diurnal Seasonality equation: $S_t = \gamma (y_t - L_t) + (1-\gamma) S_{t-m}$ (period $m = 24$ for hourly observations)
   - Forecast equation: $\hat{y}_{t+h} = L_t + \left(\sum_{i=1}^h \phi^i\right) T_t + S_{t + h \pmod{24}}$
   - The damping factor $\phi = 0.92$ prevents unrealistic linear extrapolation at extended horizons.
2. **Persistence Baseline Comparison**:
   - Every training run benchmark-evaluates the candidate model against a naive Persistence baseline ($\hat{y}_{t+h} = y_t$) on the same hold-out test set to ensure genuine predictive capability.

### 10.3 Supported Forecast Horizons
- **1 hour (`1h`)**: Immediate short-term outlook.
- **6 hours (`6h`)**: Half-day planning for commuting and outdoor activities.
- **12 hours (`12h`)**: Day/night transition projection.
- **24 hours (`24h`)**: Standard next-day planning forecast.
- **48 hours (`48h`)**: Two-day outlook (marked with `high_uncertainty`).
- **72 hours (`72h`)**: Three-day trend horizon (marked with `high_uncertainty`).

### 10.4 Historical Data Requirements & Quality Rules
- **Minimum Sample Threshold**: Minimum 24 chronological observations required for model training and forecasting.
- **Chronological Splitting**: Chronological partitions (70% train, 15% validation, 15% test) without random shuffling to strictly prevent data leakage.
- **Simulated vs. Real Data**: Verified CPCB data is prioritized. When real data is sparse, simulated data is accepted with explicit `is_simulated=True` flags and disclaimer notices.
- **Missing Data Detection**: Missing intervals ($> 3$ hours) between consecutive observations are identified and logged.

### 10.5 Weather and Meteorological Integration
- Powered by an asynchronous client connecting to **Open-Meteo** (`https://api.open-meteo.com/v1/forecast`).
- Integrates temperature, relative humidity, wind speed, wind direction, and surface pressure.
- Incorporates in-memory caching (15-minute TTL), 10s timeouts, and graceful degradation (forecasting proceeds without failure if meteorological telemetry is unavailable).

### 10.6 Model Evaluation & Metrics
- **Mean Absolute Error (MAE)**: $\frac{1}{n} \sum |y - \hat{y}|$
- **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{n} \sum (y - \hat{y})^2}$
- **Mean Absolute Percentage Error (MAPE)**: $\frac{100\%}{n} \sum \frac{|y - \hat{y}|}{\max(y, 1)}$
- Metrics are calculated overall and partitioned per forecast horizon ($1\text{h}, 6\text{h}, 12\text{h}, 24\text{h}$).

### 10.7 Uncertainty Estimation & Prediction Intervals
- Empirical residual standard deviation $\sigma_e$ computed from validation residuals.
- Interval half-width expands with the square root of horizon step:
  $$\text{SE}(h) = \sigma_e \cdot \sqrt{1 + \frac{h}{24}}$$
  $$\text{Interval} = \left[\max\left(0, \hat{y}_h - 1.645 \cdot \text{SE}(h)\right), \min\left(500, \hat{y}_h + 1.645 \cdot \text{SE}(h)\right)\right]$$
- If validation observations are fewer than 6, uncertainty status is explicitly reported as `unavailable`.

### 10.8 Forecasting REST API Endpoints (`/api/v1/forecast`)
| Method | Path | Summary | Protection |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/forecast/aqi` | Standard predictions for supported horizons (`1h` to `72h`) with uncertainty bounds | Public |
| `GET` | `/api/v1/forecast/hourly` | Sequential hourly predictions up to 72 hours | Public |
| `GET` | `/api/v1/forecast/daily` | Calendar-day aggregated forecast summaries (min, max, avg, predominant category) | Public |
| `GET` | `/api/v1/forecast/history` | Historical forecast execution runs with out-of-sample evaluation metrics | Public |
| `GET` | `/api/v1/forecast/model-status` | Operational status, model version, readiness, and baseline comparison | Public |
| `POST` | `/api/v1/forecast/generate` | Trigger on-demand model training and prediction persistence run | Admin (`X-Admin-Secret`) |

### 10.9 Model Assumptions & Limitations
- **Prediction Disclaimer**: All forecasts are mathematical modeled estimates and do not represent guaranteed future environmental measurements.
- **Atmospheric Phenomena**: Extreme localized pollution spikes (e.g. episodic biomass burning, industrial accidents, localized firecrackers) cannot be fully anticipated by statistical models without real-time emissions data.
- **Horizon Decay**: Forecast confidence degrades naturally as the time horizon extends beyond 24 hours.

---

## 11. Interactive API Documentation

When the server is running, the interactive Swagger UI and schema specifications are accessible at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
