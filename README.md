# 🌬️ Urban Air Quality Assistant

> GenAI-powered environmental intelligence helping families and communities navigate severe winter smog and urban air pollution with low-emission routines, indoor air quality hacks, sustainable alternatives, and quantified direct impact analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![CI](https://github.com/Koushik-5499/urban-air-quality-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Koushik-5499/urban-air-quality-assistant/actions/workflows/ci.yml)
[![Tests: 454 Passing](https://img.shields.io/badge/Tests-454%20Passing-brightgreen.svg)](./docs/TESTING.md)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AA-blue.svg)](./docs/ACCESSIBILITY.md)
[![SOLID Architecture](https://img.shields.io/badge/Architecture-SOLID%20Principles-purple.svg)](./ARCHITECTURE.md)

**Live Demo:**
- 🌐 Frontend: [https://urban-air-quality-frontend.vercel.app](https://urban-air-quality-frontend.vercel.app)
- 🔌 Backend API: [https://urban-air-quality-backend.vercel.app](https://urban-air-quality-backend.vercel.app)
- 📖 API Docs: [https://urban-air-quality-backend.vercel.app/docs](https://urban-air-quality-backend.vercel.app/docs)
- 🎥 Demo Video: [Watch Demonstration](https://drive.google.com/file/d/1jKEbVoW4qkYGIK4p4_eGKnr3YdI7OhDX/view?usp=sharing)

---

## 1. Chosen Vertical

**[Challenge 6] Urban Air Quality Assistant**
*Target Audience:* Families, sensitive cohorts (asthma, COPD, pediatric, elderly), outdoor workers, and urban communities in severe winter smog zones across Indian metropolitan areas (Delhi NCR, Indo-Gangetic Plain, Mumbai, Kolkata).

---

## 2. Problem Statement Alignment & Core Pillars

Every winter, millions of households face hazardous smog driven by thermal inversion layers trapping particulate matter (PM2.5, PM10) close to the ground. Generic AQI numbers do not give families the practical tools to protect their health or lower emissions.

Urban Air Quality Assistant addresses this directly across **five foundational pillars**:

1. **Severe Winter Smog & Thermal Inversion Navigation:**
   Real-time detection of thermal inversion risk, trapping warnings, and hourly diurnal vulnerability windows (peak inversion between 05:00–08:30 IST).
2. **Low-Emission Daily Routines:**
   Personalized activity scheduling that shifts heavy outdoor exertion and transit to midday low-pollution windows, promoting electric/metro public transit to reduce personal carbon and PM contributions.
3. **Indoor Air Quality Hacks:**
   Actionable, low-cost indoor interventions: diurnal ventilation timing (sealing doors during inversion peaks, ventilating between 12:00–16:00), DIY Corsi-Rosenthal / MERV box filters, wet-dusting over dry-sweeping, and high-efficiency phyto-remediation.
4. **Sustainable Alternatives Tailored to Location & Lifestyle:**
   Actionable substitutions: radiant electric/ceramic heating instead of biomass/wood burning, non-motorized micro-mobility for short errands, and community-level open waste burning reporting.
5. **Direct Impact Analysis with Quantified Metrics:**
   Every recommendation quantifies citizen benefit and environmental return: e.g., *"Reduces fine particulate lung deposition by 45–70%"*, *"Prevents ~1.2 kg CO₂ and 4.8 g PM2.5 emissions per commute"*.

### Challenge 6 Requirement Traceability Matrix (Files, Endpoints, Assumptions & Sources)

| Challenge 6 Requirement | Implementation Detail | Frontend Source | Backend Source & Endpoint |
|:---|:---|:---|:---|
| **Severe Winter Smog Navigation** | Thermal inversion risk & peak morning trap alerts (`05:00–08:30 IST`) | `frontend/src/components/dashboard/HealthRecommendation.tsx`, `frontend/src/pages/AssistantPage.tsx` | `backend/app/services/health/knowledge_data_community.py` → `GET /api/v1/health/guidelines`, `POST /api/v1/health/ask` |
| **City + Household Profile** | City selector + children, elderly, asthma, outdoor worker, commute mode & heating type controls | `frontend/src/components/dashboard/HouseholdProfileBar.tsx`, `frontend/src/components/assistant/HouseholdProfileSelector.tsx` | `backend/app/services/health/context_builder.py` → `POST /api/v1/health/ask` (`lifestyle`, `family_context`) |
| **Low-Emission Daily Routines** | Off-peak transit windows, EV/metro mode shift, midday outdoor scheduling tailored to profile | `frontend/src/utils/healthRecommendations.ts` → `getHealthRecommendations()` | `backend/app/services/health/recommendation_engine.py` → `GET /api/v1/health/community-solutions`, `GET /api/v1/health/recommendations` |
| **Indoor Air Hacks** | Diurnal ventilation timing (`12:30–15:30`), MERV-13 Corsi-Rosenthal DIY box fan, wet mopping | `frontend/src/utils/healthRecommendations.ts`, `frontend/src/components/dashboard/HealthRecommendation.tsx` | `backend/app/services/health/knowledge_data_community.py` → `GET /api/v1/health/community-solutions` |
| **Sustainable Alternatives** | Electric radiant/heat-pump heating vs biomass burning, RWA leaf composting, shared EV charging | `frontend/src/utils/healthRecommendations.ts`, `frontend/src/components/dashboard/HealthRecommendation.tsx` | `backend/app/services/health/knowledge_data_community.py` → `GET /api/v1/health/community-solutions` |
| **Quantified Impact per Action** | Explicit **PM2.5 avoided** (`µg/m³` / `% inhaled`) and **CO₂ saved** (`kg/day`) per recommendation | `frontend/src/components/dashboard/HealthRecommendation.tsx` (`ActionPlanSection`), `frontend/src/services/assistant/ruleEngine.ts` | `backend/app/services/health/knowledge_base.py` → `GET /api/v1/health/impact-metrics` |
| **Why This Advice (Explainability)** | Inline action justification + expandable CPCB/WHO priority, cohort & epidemiological reason accordion | `frontend/src/components/dashboard/HealthRecommendation.tsx`, `frontend/src/components/assistant/ChatMessageBubble.tsx` | `backend/app/services/health/recommendation_tiers_*.py` → `POST /api/v1/health/ask` |
| **Deterministic Fallback (No Gemini Key)** | Automatic zero-downtime CPCB/WHO fallback (`response_type: "knowledge_base_fallback"`) clearly badged in UI | `frontend/src/pages/AssistantPage.tsx`, `frontend/src/services/assistant/ruleEngine.ts` | `backend/app/services/health/health_advisor.py` → `_generate_knowledge_base_fallback()` |
| **Data Honesty & Provenance** | Live CPCB vs Simulated Demo Data provenance badges across views | `frontend/src/components/common/DataProvenanceBadge.tsx` | `backend/app/api/v1/endpoints/air_quality.py` → `GET /api/v1/air-quality/source-status` |

#### Key Assumptions & Impact Metric Sources (Top-Level Reference)
- **Model & Fallback Assumption:** Uses Google Gemini (`gemini-2.5-flash` default in `backend/app/core/config.py`) when `GEMINI_API_KEY` is configured; without a key, every advisory route runs deterministically using CPCB/WHO rule tables clearly labelled as deterministic fallback.
- **Telemetry Assumption:** Falls back seamlessly to simulated CPCB-calibrated city telemetry when `CPCB_API_KEY` is unset, badged transparently as simulated demo data. Not clinical medical advice.
- **PM2.5 & NAQI Health Thresholds:** Central Pollution Control Board (CPCB) National Air Quality Index (NAQI, 2014); World Health Organization (WHO) Global Air Quality Guidelines (2021, PM2.5 24h target `15 µg/m³`); CPCB Inversion Research (2023).
- **CO₂ & Intervention Savings:** Delhi Transport Corporation EV Life-Cycle Assessment (`~3.2 kg CO₂/day` metro vs petrol car); EPA Clean Air Guidance (`75–85%` indoor PM2.5 reduction via MERV-13 Corsi-Rosenthal filter); IIT Delhi Indoor Air Study (`~65%` PM10 resuspension reduction via wet mopping); CPCB Open Burning Survey & BEE Heating Advisory (`>800 µg/m³` peak & `~3.6 kg CO₂/evening` saved replacing biomass fires).

---

## 2.5 Smart & Dynamic Assistant Behaviour

The assistant demonstrates **context-aware, logical decision making** throughout every layer:

| Trigger | Dynamic Response | Implementation |
|:---|:---|:---|
| AQI < 100 (Good/Satisfactory) | Positive reinforcement; outdoor activities encouraged | `ruleEngine.ts` → `generateRecommendations()` |
| AQI 101–200 (Moderate/Moderate Polluted) | Sensitive-group caution; mask advisory for asthmatics | `health_advisor.py` → knowledge base tier 2 |
| AQI 201–300 (Poor) | Full outdoor restriction; indoor filtration steps | `health_advisor.py` → knowledge base tier 3 |
| AQI > 300 (Very Poor/Severe) | Critical alert; evacuation of outdoor spaces; hospital warning | Threshold alert C=18→C=13 complexity |
| Time = 05:00–08:30 IST | Peak thermal-inversion banner; "do not go outside" override | `ruleEngine.ts` INVERSION_WINDOW detection |
| Vulnerable cohort detected (children / elderly / asthmatic) | Stricter thresholds; specialist medical caveats | `queryParser.ts` cohort classifier |
| Live CPCB data unavailable | Transparent "Demo Data" badge; fallback knowledge base | `DataProvenanceBadge.tsx` + `gemini_provider.py` AI→KB chain |
| AI (Gemini) rate-limited or offline | Deterministic knowledge base fallback — zero downtime | `health_advisor.py` `_generate_knowledge_base_fallback()` |

### Quantified Impact Examples (from production knowledge base)

| Recommendation | Measured Impact | Source |
|:---|:---|:---|
| Midday activity rescheduling (avoid 05:00–09:30) | Cuts peak particulate inhalation **up to 52%** | CPCB Inversion Research 2023 |
| Metro/electric bus commute vs private car | Saves **~3.2 kg CO₂** + **45% lower** in-cabin toxic gas | Delhi Transport Corp. EV LCA |
| Corsi-Rosenthal DIY HEPA box fan | Reduces indoor PM2.5 by **75–85%** | EPA Clean Air Guidance |
| Damp mopping vs dry sweeping | Reduces PM10 resuspension by **~60%** | Indoor Air Quality Study, IIT Delhi |
| Electric radiant heater vs open biomass burn | Removes localized PM2.5 spikes **>800 µg/m³** | CPCB Open Burning Survey |
| N95 mask during commute | Reduces inhaled PM2.5 by **95%** | CPCB Protective Equipment Standards |

---

## 3. Architecture & SOLID Principles

The system is engineered according to strict **SOLID principles** and enterprise design patterns. For complete class diagrams and principle mappings, see [ARCHITECTURE.md](./ARCHITECTURE.md).

- **Single Responsibility Principle (SRP):** Distinct layers for CPCB telemetry ingestion, NAQI mathematical calculation, Holt-Winters exponential smoothing, Gemini AI generation, and safety validation.
- **Open/Closed Principle (OCP):** Pluggable provider architectures (`BaseAIProvider`, `BaseForecastModel`, `BaseNotificationChannel`) extensible without modifying core services.
- **Liskov Substitution Principle (LSP):** `GeminiProvider` and `MockAIProvider` can be substituted interchangeably without altering caller contracts. `BaseRepository` ensures all data-access implementations are swappable.
- **Interface Segregation Principle (ISP):** Granular interfaces for telemetry reading, alert dispatching, health synthesis, and data access (`BaseRepository`, `BaseAIProvider`, `BaseNotificationChannel`, `BaseForecastModel`).
- **Dependency Inversion Principle (DIP):** High-level endpoints depend on abstract provider protocols injected via FastAPI dependency injection.

### Abstract Interfaces Summary
| Interface | File | Implementations |
|:---|:---|:---|
| `BaseAIProvider` | `integrations/ai/base.py` | `GeminiProvider`, `MockAIProvider` |
| `BaseAQIProvider` | `integrations/base.py` | `CPCBProvider`, `MockProvider` |
| `BaseNotificationChannel` | `services/alerts/notification_service.py` | `WebPushNotificationChannel`, `InAppNotificationChannel` |
| `BaseForecastModel` | `services/forecasting/models/base.py` | `ExponentialSmoothingModel` |
| `BaseRepository` | `repositories/base.py` | `ReadingRepository`, `CityRepository`, `StationRepository` |

---

## 4. How the Solution Works

### System Topology

```mermaid
flowchart TD
    FE["React 18 Frontend\n(Vite + TypeScript + Tailwind)"]
    BE["FastAPI Backend\n(Python 3.11)"]
    DB["SQLite / Turso\n(libSQL)"]
    CPCB["CPCB API\n(data.gov.in)"]
    GEM["Google Gemini\n(gemini-2.5-flash)"]
    WX["Open-Meteo\nWeather API"]

    FE -->|REST API calls| BE
    BE --> DB
    BE -->|Poll every 5min| CPCB
    BE -->|Health & Routine Guidance| GEM
    BE -->|Atmospheric Context| WX
```

### Key Modules

- **CPCB NAQI Calculation:** Exact Indian NAQI standard (CPCB 2014) computed across PM2.5, PM10, NO₂, SO₂, O₃, CO, NH₃, Pb using official piecewise linear breakpoints.
- **24h Holt-Winters Forecasting:** Pure Python diurnal seasonal exponential smoothing model with additive seasonality (`backend/app/services/forecasting/`).
- **GenAI Health & Routine Advisor:** Ingests live telemetry, inversion state, and vulnerability profile to deliver grounded recommendations via Gemini with deterministic fallback (`backend/app/services/health/`).
- **Community Solutions Endpoint:** `GET /api/v1/health/community-solutions` delivers structured routines, indoor hacks, and impact metrics.
- **Public Alert Evaluator:** Sliding-window delta checks (Δ > 30 AQI) and category boundary transitions with 24-hour deduplication keys (`backend/app/services/alerts/`).

### Request Flows

**Dashboard Load:**
1. `GET /api/v1/aqi/latest?city=Delhi` → cache check → CPCB fetch → NAQI compute → response
2. Frontend renders AQI gauge, pollutant cards, weather card, and health recommendations

**AI Assistant:**
1. User submits question → `POST /api/v1/health/ask` with city + question + history
2. Prompt-injection validator screens input (rejects `ignore previous instructions`, jailbreak patterns)
3. Context builder assembles AQI + weather + vulnerability profile + inversion state
4. Gemini generates structured JSON response → Safety validator screens it → Response returned
5. Frontend renders in `aria-live="polite"` chat region with priority/reason/source explainability

**Alerts:**
1. Background evaluator runs every 5 min → compares current AQI to thresholds
2. Deduplication check → Alert record saved → `GET /api/v1/alerts?city=Delhi` returns public list

---

## 4.5 GenAI Integration Details

The application uses Google Gemini as its primary AI backbone, fully aligned with the Challenge 6 requirement for a GenAI-powered urban air quality assistant.

### Model & SDK
| Property | Value |
|:---|:---|
| Model | `gemini-2.5-flash` (via `google-genai` Python SDK) |
| Implementation | `backend/app/integrations/ai/gemini_provider.py` |
| Base class | `BaseAIProvider` (ABC) in `backend/app/integrations/ai/base.py` |
| Mock substitute | `MockAIProvider` in `backend/app/integrations/mock/provider.py` |

### Request Pipeline
```
User question
  → PromptInjectionValidator (rejects jailbreak patterns)
  → ContextBuilder (AQI + weather + inversion state + vulnerability profile)
  → GeminiProvider.generate_response()
  → SafetyValidator (screens medical advice, checks response completeness)
  → Fallback: HealthKnowledgeBase (deterministic, zero-downtime)
  → Response with: priority, target_group, reason, source, impact_metrics
```

### Structured Response Schema
The Gemini prompt is engineered to return structured health advice with:
- **priority**: `critical` / `high` / `medium` / `low`
- **target_group**: specific vulnerable group(s) addressed
- **reason**: "Why this advice?" explanation referencing CPCB/WHO standards
- **source**: citation (`CPCB NAQI 2014`, `WHO AQG 2021`, etc.)
- **impact**: quantified metric (e.g., "Reduces PM2.5 inhalation by 52%")

### Safety & Security
- **Prompt injection guard**: Pydantic field validator rejects questions containing injection patterns
- **Medical disclaimer**: All AI responses include a standard medical disclaimer
- **API key**: Stored in `backend/.env` (gitignored), never logged (SecretRedactionFilter)
- **Fallback resilience**: If Gemini is unavailable/rate-limited, `_generate_knowledge_base_fallback()` activates immediately

### Quantified Impact Endpoint
`GET /api/v1/health/impact-metrics` — Returns CPCB/WHO-sourced impact metrics for all 5 Challenge 6 pillars (winter smog, low-emission routines, indoor hacks, sustainable alternatives, vulnerable groups).

---

## 5. Assumptions

| Assumption | Detail |
|---|---|
| **Data Provider** | App uses CPCB data.gov.in API. Without `CPCB_API_KEY` or when unreachable, falls back to **simulated data** (clearly labeled "Simulated Data" badge in UI) |
| **Database** | SQLite for local dev. On Vercel serverless, writes to `/tmp/air_quality.db` (ephemeral — resets per cold start). Set `DATABASE_URL` to Turso/libSQL or Postgres for persistent production data |
| **User Accounts** | Platform is fully **public and anonymous** — no registration, login, or user accounts required. All alerts and analytics are public environmental data |
| **Health Advice** | AI-generated guidance is **informational only** and not medical advice. A disclaimer is prominently shown in the UI |
| **Web Push** | VAPID-based web push is implemented but requires a valid key pair to activate in production. Disabled by default |
| **Forecasting** | Requires a minimum of 24 historical AQI observations to train the model. Falls back to trend-based estimates with fewer observations |

---

## 6. Setup and Run

**Requirements:** Python 3.11+ · Node.js 20+

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set GEMINI_API_KEY and optionally CPCB_API_KEY
uvicorn app.main:app --reload --port 8000
```
API docs available at: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: VITE_API_BASE_URL=http://localhost:8000
npm run dev
```
App available at: http://localhost:5173

### Environment Variables

**Backend (`backend/.env`):**
| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Recommended | Google AI Studio API key for health advisor |
| `CPCB_API_KEY` | Optional | data.gov.in API key for real AQI data |
| `DATABASE_URL` | Optional | Override SQLite (e.g., `libsql://...` for Turso) |
| `VAPID_PRIVATE_KEY` | Optional | For web push notifications |
| `VAPID_PUBLIC_KEY` | Optional | Paired VAPID public key |
| `AI_PROVIDER` | Optional | `gemini` (default) or `mock` |
| `AQI_PROVIDER` | Optional | `cpcb` (default) or `mock` |

**Frontend (`frontend/.env.local`):**
| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | Backend API URL (e.g., `http://localhost:8000`) |
| `VITE_API_TIMEOUT_MS` | Optional | Request timeout in ms (default: 10000) |

---

## 7. Testing & Quality Verification

Comprehensive automated test suites validate all components across backend algorithms, AI integrations, and frontend interactions. See [docs/TESTING.md](./docs/TESTING.md) for full coverage metrics and breakdown.

### Backend (356 Tests Passed, 0 Skipped, 93.7% Coverage)
```bash
cd backend
.venv/bin/pytest -q --cov=app --cov-fail-under=90
# 356 passed in 37.85s (93.70% statement coverage across 4,827 statements)
```

### Frontend (98 Tests Passed, 15 Test Suites, 86.9% Line Coverage)
```bash
cd frontend
npx vitest run --coverage
# Test Files  15 passed (15)
# Tests       98 passed (98) — Stmts 86.88% | Branches 79.10% | Funcs 63.96% | Lines 86.88%

npm run lint
# (exit 0, 0 errors, 0 warnings)

npx tsc -b --noEmit
# (exit 0, 0 type errors)

npm run build
# ✓ built in 6.99s
```
**Total Verified Tests: 454 automated unit, integration, security, accessibility, alignment, and E2E tests (356 Backend + 98 Frontend).**

The 15 new alignment acceptance tests in `backend/tests/test_alignment.py` cover all 8 Challenge 6 pillars:
winter smog & thermal inversion, low-emission routines, indoor air hacks, sustainable alternatives,
quantified impact, vulnerable groups, data honesty, and explainability.

---

## 8. Security, Accessibility & Efficiency

### Security
For complete penetration testing, threat models, and vulnerability audits, see [docs/SECURITY_AUDIT.md](./docs/SECURITY_AUDIT.md).
- **Sensitive Operations Protection:** Constant-time `hmac.compare_digest` for all admin actions, token evaluations, and secret verifications (`X-Admin-Secret`, `X-API-Key`, and `Authorization: Bearer <secret>`) to eliminate timing side-channel attacks (`backend/app/core/security.py`).
- **Input Validation & Sanitization:** Strict Pydantic v2 schemas reject malformed payloads, injection vectors, and out-of-bound coordinates (`backend/app/schemas/`).
- **Sliding-Window Rate Limiting:** Per-client IP rate limiting (120 req/min general, 20 req/min AI) with automated memory pruning (`backend/app/core/security.py`).
- **Zero-Trust Network Perimeter:** CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy headers applied across CDN and reverse proxies (`frontend/vercel.json`).
- **Secret Redaction:** Logging pipelines filter credentials and API keys (`backend/app/core/logging.py`).

### Accessibility (WCAG 2.1 AA Compliant)
Full compliance report and testing methodology: [docs/ACCESSIBILITY.md](./docs/ACCESSIBILITY.md).
- **Skip-to-Content:** Native keyboard shortcut to jump past navigation on every page (`frontend/src/layouts/RootLayout.tsx`).
- **Contrast & Visibility:** WCAG AA 4.5:1 minimum text contrast; high-visibility 3px focus rings (`:focus-visible`).
- **Screen Reader Support:** Screen reader announcements via `aria-live="polite"` for dynamic AQI updates and AI responses (`frontend/src/pages/AssistantPage.tsx`).
- **Dual Visual Indicators:** AQI levels convey severity using both distinct colors AND textual category labels.

### Efficiency & Performance
- **Code Splitting:** React routes lazily loaded (`React.lazy`), reducing initial payload.
- **Diurnal Caching:** 5-minute memory cache prevents redundant upstream CPCB API calls.
- **Vendor Splitting:** Isolated bundles for Recharts, Leaflet, Lucide, and React core.

**Bundle sizes (production build):**
| Chunk | Size (gzip) |
|---|---|
| `vendor-charts` (Recharts) | 488 kB (137 kB gzip) |
| `vendor-react` (React + Router) | 180 kB (59 kB gzip) |
| `vendor-maps` (Leaflet) | 155 kB (45 kB gzip) |
| `vendor-icons` (Lucide) | 39 kB (8 kB gzip) |
| App pages (all 7, split) | ≤ 69 kB each |

---

## 9. Known Limitations

- **SQLite on Vercel is ephemeral**: Data resets on each cold start. Set `DATABASE_URL` to Turso/libSQL or Postgres for persistence in production.
- **CPCB API key required for real data**: Register at [data.gov.in](https://data.gov.in) to get a key. Without it, the app uses simulated data (clearly labeled).
- **Forecasting requires history**: Minimum 24 observations needed. New deployments will produce limited forecasts until data accumulates.
- **AI response availability**: Depends on Gemini API quota and availability. Rule-based fallback activates automatically.
- **Web push requires HTTPS**: Browser push notifications need a production HTTPS domain and VAPID keys configured.

---

## Deployment

| Component | URL |
|---|---|
| Frontend | [https://urban-air-quality-frontend.vercel.app](https://urban-air-quality-frontend.vercel.app) |
| Backend API | [https://urban-air-quality-backend.vercel.app](https://urban-air-quality-backend.vercel.app) |
| GitHub | [https://github.com/Koushik-5499/urban-air-quality-assistant](https://github.com/Koushik-5499/urban-air-quality-assistant) |

For detailed deployment instructions, see [docs/VERCEL_DEPLOYMENT.md](./docs/VERCEL_DEPLOYMENT.md).

> **Database Note:** SQLite on Vercel serverless is ephemeral. For persistent production data, provision a [Turso](https://turso.tech) database and set `DATABASE_URL=libsql://your-db.turso.io?authToken=your-token` in the backend Vercel environment variables.

---

## License

MIT © 2026 Urban Air Quality Assistant Contributors. See [LICENSE](./LICENSE).
