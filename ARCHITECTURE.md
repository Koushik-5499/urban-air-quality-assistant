# Urban Air Quality Assistant – Architecture & Technical Design

This document details the architectural topology, software design patterns, and rigorous implementation of **SOLID principles** across the Urban Air Quality Assistant platform.

---

## 1. High-Level System Architecture

The Urban Air Quality Assistant is an enterprise-grade, public environmental monitoring and AI-powered health advisory platform. It operates a decoupled, modern architecture:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT TIER (Vite + React 18)                           │
│  - Reactive Dashboard & Gauges           - City Search & Leaflet Geo-Map              │
│  - AI Health Advisor Chat & Suggested Qs - Historical Analytics & Trends Charts       │
│  - Live Public Ambient Alert Banners     - WCAG 2.1 AA Accessible UI (Tailwind CSS)   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON API (REST v1)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               GATEWAY & SECURITY MIDDLEWARE                            │
│  - SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options: DENY, Referrer-Policy)       │
│  - RateLimitMiddleware (Sliding window per IP: 120 rpm general, 20 rpm AI)            │
│  - RequestSizeLimitMiddleware (1 MB DoS payload protection)                            │
│  - CORS Middleware (Configured origin allowlisting, credential isolation)              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION TIER (FastAPI)                              │
│  ┌───────────────────────┬───────────────────────┬──────────────────────────────────┐  │
│  │     Routers (v1)      │    Service Layer      │      Integrations & AI           │  │
│  │  - /api/v1/aqi        │  - AQICalculator      │  - GeminiProvider (google-genai) │  │
│  │  - /api/v1/health     │  - HealthAdvisor      │  - ContextBuilder & Grounding    │  │
│  │  - /api/v1/forecast   │  - ForecastService    │  - HealthSafetyValidator         │  │
│  │  - /api/v1/alerts     │  - AlertService       │  - CPCB / Mock Data Ingestion    │  │
│  │  - /api/v1/history    │  - HistoryService     │  - WebPushChannel (VAPID)        │  │
│  └───────────────────────┴───────────────────────┴──────────────────────────────────┘  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA ACCESS & PERSISTENCE                                │
│  - SQLAlchemy 2.0 ORM with Async/Sync Engine abstraction                               │
│  - Alembic Database Migrations                                                         │
│  - SQLite (Local development / ephemeral Vercel Serverless `/tmp`)                     │
│  - Indexed Tables: `cities`, `stations`, `pollutant_measurements`, `aqi_readings`,     │
│    `alerts`, `forecasts`                                                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. SOLID Principles Implementation Matrix

The codebase strictly adheres to the five core **SOLID principles of Object-Oriented and Modular Software Design**:

| Principle | Architectural Manifestation | Concrete Files & Classes |
|:---|:---|:---|
| **S** – Single Responsibility | Routers handle HTTP; Services execute business logic; Repositories manage persistence; Providers manage external integrations; Validators enforce safety. | `app/api/v1/endpoints/health.py`<br>`app/services/health/health_advisor.py`<br>`app/services/health/safety_validator.py` |
| **O** – Open / Closed | System components are open for extension through abstract base interfaces, but closed for modification. New providers and models can be added without modifying consumer services. | `app/integrations/ai/base.py`<br>`app/services/forecasting/models/base.py`<br>`app/services/alerts/notification_service.py` |
| **L** – Liskov Substitution | Subclasses and concrete implementations can be substituted transparently for their base abstractions without breaking application invariants or tests. | `GeminiProvider` & `MockAIProvider`<br>`ExponentialSmoothingModel` & `BaselineModel`<br>`WebPushChannel` & `InAppAlertChannel` |
| **I** – Interface Segregation | Clients depend on focused, purpose-built interfaces and schemas rather than fat, monolithic contracts. | `AICompletionRequest` vs `AQIContextSnapshot`<br>`HealthAskRequest` vs `HealthAskResponse`<br>`RecommendationItem` |
| **D** – Dependency Inversion | High-level business services do not depend on low-level database or network primitives; both depend on abstractions injected via FastAPI `Depends()`. | `get_db` session dependency<br>`get_settings` configuration injection<br>`get_health_advisor` & `get_alert_service` |

---

### Deep Dive: SOLID Implementation Details

#### 1. Single Responsibility Principle (SRP)
Each module has one, and only one, reason to change:
- **API Endpoints (`app/api/v1/endpoints/`)**: Responsible exclusively for request payload validation, status codes, query pagination, and response wrapping.
- **Service Layer (`app/services/`)**:
  - `AQICalculator`: Encapsulates pure mathematical CPCB NAQI sub-index formulas and breakpoint interpolation without database or HTTP side-effects.
  - `ContextBuilder`: Extracts and formats verified environmental observations from the database into an immutable `AQIContextSnapshot`.
  - `RecommendationEngine`: Deterministically maps AQI tiers to structured, proportional health precautions and Challenge 6 pillars.
  - `HealthSafetyValidator`: Executes defensive input sanitization, length boundaries, and medical prescription redaction.
- **Data Repositories / Models (`app/models/`)**: Focus solely on SQLAlchemy relational mapping, foreign key constraints, and indexing.

#### 2. Open / Closed Principle (OCP)
The system is architected for frictionless extension:
- **AI Integration**: Defined via `BaseAIProvider` (`app/integrations/ai/base.py`). Adding an alternative LLM provider (e.g. Anthropic Claude, Mistral, or a local Ollama model) requires only subclassing `BaseAIProvider` and implementing `generate_response()`. The `HealthAdvisorService` consumes `BaseAIProvider` and remains completely untouched.
- **Forecasting Models**: Defined via `BaseForecastModel` (`app/services/forecasting/models/base.py`). The `ForecastModelFactory` produces models dynamically (`exponential_smoothing`, `holt_winters`, `ets`). Adding a machine-learning model (e.g. Prophet or LSTM) requires implementing `fit_predict()` without modifying existing forecasters.
- **Alert Dispatch**: Alerting channels implement `BaseNotificationChannel`. Adding SMS or webhook delivery channels does not require changes to `AlertService`.

#### 3. Liskov Substitution Principle (LSP)
Subclasses honor the complete behavioral contract of their abstractions:
- `MockAIProvider` can be substituted for `GeminiProvider` across test suites and offline environments; both return standard `AICompletionResponse` objects without unexpected exceptions.
- `MockAirQualityProvider` can be substituted for `CPCBClient`; both produce standardized `ObservationRecord` streams adhering to the National Air Quality Standard schema.
- `WebPushNotificationChannel` and `InAppNotificationChannel` implement `BaseNotificationChannel` (`app/services/alerts/notification_service.py`) and can be substituted transparently across delivery pipelines.

#### 4. Interface Segregation Principle (ISP)
Interfaces and schemas are kept lean and decoupled:
- Rather than passing large, coupled database models into the AI layer, the service constructs a concise, decoupled `AQIContextSnapshot`.
- The frontend chat interface depends only on `ChatMessage`, `HealthAskRequest`, and `HealthAskResponse`, isolating presentation state from backend database schemas.
- Pydantic v2 schemas use `ConfigDict(from_attributes=True)` for strict separation between serialization schemas and ORM entities.

#### 5. Dependency Inversion Principle (DIP)
High-level modules rely on abstractions, not concrete implementations:
```python
# Routers receive dependencies injected dynamically at runtime
@router.post("/ask", response_model=HealthAskResponse)
async def ask_health_assistant(
    request: HealthAskRequest,
    db: Session = Depends(get_db),
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> HealthAskResponse:
    return await advisor.ask(db=db, request=request)
```
- Database sessions (`get_db`) are yielded with automatic commit/rollback and connection closing.
- In automated test suites, database sessions and external services are overridden cleanly using `app.dependency_overrides` without touching business logic or database engines.

---

## 3. Challenge 6 Domain Architecture

The platform directly aligns with **Challenge 6: Urban Air Quality Assistant**, architected across five pillars:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CHALLENGE 6 SOLUTION PILLARS                              │
├──────────────────────────┬──────────────────────────┬──────────────────────────────────┤
│ 1. Winter Smog &         │ 2. Low-Emission Daily    │ 3. Indoor Air Quality            │
│    Inversion Protection  │    Routines              │    Hacks                         │
│ • Nocturnal inversion    │ • Off-peak commute       │ • Diurnal ventilation timing     │
│   trapping alerts        │   rescheduling (7-10 AM) │   (12:30 PM - 3:30 PM only)      │
│ • Pediatric & elderly    │ • Electrified metro trip │ • DIY Corsi-Rosenthal boxes      │
│   morning shelter rules  │   substitution           │ • Wet mopping (zero dry sweep)   │
│ • Community anti-biomass │ • Midday workout shifts  │ • Phyto-remediation houseplants  │
│   burning vigilance      │   (1:00 PM - 4:00 PM)    │   (Snake Plant, Areca Palm)      │
├──────────────────────────┴──────────────────────────┴──────────────────────────────────┤
│ 4. Sustainable Alternatives Tailored to Location & Lifestyle                           │
│ • Clean electric ceramic radiant heating vs unvented solid-fuel braziers               │
│ • Residential welfare association (RWA) shared EV charging bays & solar rooftop        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. Direct Impact Analysis & Quantification                                             │
│ • Metro transit: Saves 3.2 kg CO2 & 18g NOx per passenger daily; cuts PM2.5 by 45%     │
│ • Diurnal ventilation: Reduces indoor particle infiltration by 70-80%                  │
│ • DIY HEPA filtration: Lowers bedroom PM2.5 from >250 µg/m³ to <35 µg/m³ in 45 minutes │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Security Architecture & Sensitive Operation Protection

The backend enforces defense-in-depth across all sensitive operations:

1. **Privileged Operations (`X-Admin-Secret`)**:
   - Background data synchronization (`POST /api/v1/air-quality/sync`)
   - Alert evaluation cycle triggering (`POST /api/v1/alerts/process`)
   - On-demand forecast generation (`POST /api/v1/forecast/generate`)
   - Test notification dispatch (`POST /api/v1/alerts/test-notification`)
   - **Protection Mechanism**: All admin endpoints enforce timing-safe token verification using `hmac.compare_digest(x_admin_secret.encode(), secret.encode())`. In production (`APP_ENV=production`), secrets are mandatory; unset secrets raise `HTTP 403 Forbidden`.

2. **DoS & Memory Exhaustion Protection**:
   - `RequestSizeLimitMiddleware` inspects `Content-Length` headers and rejects payloads exceeding 1 MB (`HTTP 413 Content Too Large`).
   - `RateLimitMiddleware` enforces in-memory sliding-window token bucket limits per client IP (120 req/min general, 20 req/min for AI queries, 10 req/min for administrative sync).

3. **GenAI Safety & Prompt Injection Sanitization**:
   - `HealthSafetyValidator` enforces strict length boundaries (2–500 chars for questions, max 10 conversation turns).
   - Prompt containment shields the system instruction from override attacks.
   - Regex guardrails intercept and neutralize medical prescribing language (`PRESCRIPTION_PATTERNS`).
   - All AI responses append mandatory non-medical public health disclaimers.

4. **HTTP Header Hardening**:
   - `Content-Security-Policy`: `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`
   - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`
   - `X-Frame-Options`: `DENY`
   - `X-Content-Type-Options`: `nosniff`
   - `Permissions-Policy`: `camera=(), microphone=(), geolocation=(), payment=(), usb=()`
   - `Referrer-Policy`: `strict-origin-when-cross-origin`

---

## 5. Directory Structure & Layering

```
urban-air-quality-assistant/
├── ARCHITECTURE.md                 # Architectural design and SOLID documentation
├── README.md                       # Complete platform overview, setup, and results
├── docs/
│   ├── ACCESSIBILITY.md            # WCAG 2.1 AA accessibility audit & compliance
│   ├── SECURITY_AUDIT.md           # Security controls and sensitive operation protection
│   ├── TESTING.md                  # Test execution instructions and verification numbers
│   └── VERCEL_DEPLOYMENT.md        # Serverless deployment configuration
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/       # S: Router layer (HTTP serialization & status codes)
│   │   │   ├── air_quality.py      # Telemetry & station endpoints
│   │   │   ├── alerts.py           # Public ambient alert endpoints
│   │   │   ├── aqi.py              # Real-time CPCB NAQI calculation endpoints
│   │   │   ├── forecast.py         # Multi-horizon forecast endpoints
│   │   │   ├── health.py           # GenAI health advisor & community solutions
│   │   │   └── history.py          # Historical trends & comparative analytics
│   │   ├── core/                   # Cross-cutting concerns (Security, Config, Logging)
│   │   ├── db/                     # Database connection & session management
│   │   ├── integrations/ai/        # O & L: Pluggable AI Provider layer (Base & Gemini)
│   │   ├── models/                 # SQLAlchemy ORM entity definitions
│   │   ├── schemas/                # I: Segregated Pydantic v2 schemas
│   │   └── services/               # S: Business logic domain services
│   │       ├── aqi/                # CPCB NAQI sub-index formulas & breakpoints
│   │       ├── alerts/             # Event detection & deduplication engine
│   │       ├── forecasting/        # Factory & pluggable forecasting models
│   │       ├── health/             # RecommendationEngine, ContextBuilder, KnowledgeBase
│   │       └── history/            # Statistical aggregation & trend analysis
│   ├── tests/                      # Automated test suite (154 passing tests)
│   ├── pytest.ini                  # Pytest configuration
│   └── requirements.txt            # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/             # Reusable, accessible UI components (Tailwind CSS)
    │   │   ├── assistant/          # AI chat interface & suggested prompts
    │   │   ├── dashboard/          # AQI overview, pollutant cards, health advice
    │   │   ├── analytics/          # Trend charts & forecast visualizers
    │   │   ├── maps/               # Interactive Leaflet air quality map
    │   │   └── alerts/             # Public alert feed & severity badges
    │   ├── services/               # API clients & local assistant engine
    │   ├── types/                  # Strict TypeScript interfaces
    │   └── utils/                  # NAQI breakpoints & health recommendations
    ├── package.json                # Frontend dependencies
    └── vite.config.ts              # Vite production bundler configuration
```

