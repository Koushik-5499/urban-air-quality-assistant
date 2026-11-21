# Testing Documentation — Urban Air Quality Assistant

**Project:** Urban Air Quality Assistant  
**Date:** November 20, 2026  
**Assessment Phase:** Phase 10 — Security Hardening, Testing and Reliability Verification  
**Total Tests Passing:** 204 tests (153 Backend + 51 Frontend)  
**Pass Rate:** 100%  

---

## 1. Testing Philosophy & Strategy

The Urban Air Quality Assistant uses a multi-layered testing strategy combining:
- **Backend Unit & Integration Tests (Pytest + AnyIO + HTTPX):** Testing mathematical formulas (NAQI breakpoints), database persistence, repositories, external provider abstractions, asynchronous background tasks, and security middlewares.
- **Frontend Unit & Integration Tests (Vitest + React Testing Library):** Verifying UI state, chart data transformers, alert management, and resilient API adapters with graceful offline fallback.
- **End-to-End (E2E) Simulated Journeys:** Testing the complete 12-step user path from dashboard initialization to AI consultation and multi-city comparison.
- **Static Security & Code Quality Gates:** Automated AST security scanning (`bandit`), dependency audits (`pip-audit`, `npm audit`), TypeScript compilation (`tsc -b`), and ESLint verification.

---

## 2. Test Execution Summary

| Test Layer | Test Runner | Files | Tests | Status | Execution Time |
|---|---|---|---|---|---|
| **Backend Suite** | `pytest 9.2` (Python 3.14) | 9 | 153 | **153 Passed (100%)** | ~5.5s |
| **Frontend Suite** | `vitest 2.1.9` | 8 | 51 | **51 Passed (100%)** | ~1.1s |
| **Frontend Linting** | `eslint 9.x` | All source | N/A | **0 Errors, 0 Warnings** | ~0.8s |
| **Frontend Build** | `vite build` | 2,711 modules | N/A | **Clean Build (0 Errors)** | ~4.1s |
| **Backend AST Audit** | `bandit 1.8` | 9,519 lines | N/A | **0 Vulnerabilities Found** | ~0.5s |
| **Python Dependencies**| `pip-audit` | 42 packages | N/A | **0 Known CVEs** | ~1.2s |
| **Total Test Suite** | Combined | 17 | 204 | **204 Passed (100%)** | **All Passed** |

---

## 3. Backend Test Suite (`backend/tests/`)

The backend test suite is configured via `backend/pytest.ini` and uses `httpx.AsyncClient` alongside an isolated in-memory or file-backed SQLite database fixture (`backend/tests/conftest.py`).

### 3.1 Test Modules Breakdown

1. **`test_health.py` (10 tests):**
   - Health check endpoints (`/health/live`, `/health/ready`).
   - Database ping verification and system uptime tracking.
   - Root application information and API versioning.

2. **`test_database.py` (10 tests):**
   - SQLAlchemy 2.0 schema initialization and migration checks.
   - Model relationships (`City`, `Station`, `Measurement`, `AQICalculation`, `Alert`, `NotificationLog`).
   - Foreign key integrity, unique constraints, and transaction rollback on error.

3. **`test_air_quality.py` (11 tests):**
   - City and station retrieval for the 10 supported Indian metropolitan areas.
   - Real-time measurement querying and dominant pollutant indexing.
   - Mocked external provider ingestion pipelines (OpenAQ / CPCB).

4. **`test_aqi_engine.py` (17 tests):**
   - Indian National Air Quality Index (NAQI) calculation algorithm.
   - Sub-index linear interpolation across 8 parameters ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3, NH_3, Pb$).
   - Category breakpoint classification (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
   - Dominant pollutant determination rules.

5. **`test_history.py` (21 tests):**
   - Time series aggregation (hourly, daily, weekly).
   - Historical AQI summaries and pollutant distributions.
   - Boundary checks for date filters (`start_date`, `end_date`) and pagination limits.

6. **`test_ai_advisor.py` (21 tests):**
   - Google Gemini AI prompt synthesis with real AQI context.
   - Fallback heuristic health advisory engine when external AI is unreachable.
   - Recommendation generation for sensitive populations (elderly, children, respiratory patients).
   - Prompt sanitization and medical liability disclaimer enforcement.

7. **`test_alerts.py` (30 tests):**
   - Alert threshold evaluation based on AQI and specific pollutants.
   - User notification preferences persistence (`X-User-Id`).
   - Email dispatch simulation and in-app notification inbox state transitions.

8. **`test_forecast.py` (23 tests):**
   - 24-hour predictive AQI modeling using diurnal cycles and exponential smoothing.
   - Trend analysis and confidence intervals.
   - Clearly separated forecast records from historical observations.

9. **`test_security.py` (10 tests):**
   - Standard security headers injection (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`, `Permissions-Policy`).
   - Request size limit middleware (rejects >1MB payloads with HTTP 413).
   - User ID regex validation preventing header injection and path traversal (`^[a-zA-Z0-9_\-\.]{1,64}$`).
   - Admin secret key enforcement in production mode (`verify_admin_access`).
   - Sensitive credential masking in logs (`SecretRedactionFilter`).
   - In-memory sliding-window rate limiting (HTTP 429 response on threshold breaches).
   - Date range validation in historical queries (rejects `start_date > end_date`).
   - AI health question length validation (rejects empty/oversized prompts).
   - CORS preflight and allowed origins.

---

## 4. Frontend Test Suite (`frontend/src/__tests__/`)

The frontend test suite is configured with `vitest` and operates in an isolated JSDOM environment with mocked browser APIs.

### 4.1 Test Modules Breakdown

1. **`aqi.test.ts` (3 tests):**
   - Color scale mappings and category text outputs.
   - Edge cases at category boundaries (e.g., AQI = 50, 100, 200, 300, 400).

2. **`cityData.test.ts` (5 tests):**
   - Metadata validation for 10 Indian cities (Delhi, Mumbai, Bengaluru, etc.).
   - Coordinates, default station lists, and bounding boxes.

3. **`assistantEngine.test.ts` (5 tests):**
   - Client-side intent recognition and query routing.
   - Context injection for localized air quality discussions.

4. **`apiClient.test.ts` (4 tests):**
   - Axios/Fetch wrapper error handling and retry logic.
   - Base URL configuration and default request headers.

5. **`alertService.test.ts` (4 tests):**
   - Local alert state management and threshold validation.
   - User preference synchronization.

6. **`analyticsService.test.ts` (5 tests):**
   - Statistical aggregation for trend charts.
   - Moving average calculations for pollutant concentrations.

7. **`apiIntegration.test.ts` (17 tests):**
   - Integration adapter verifying backend API endpoint mapping.
   - Fallback to mock data when backend is disconnected.
   - Serialization and deserialization of API responses.

8. **`e2eUserJourneys.test.ts` (8 tests):**
   - Comprehensive simulation of full multi-step user workflows (detailed below).

---

## 5. End-to-End User Journeys (12-Step Test Matrix)

The test suite in `frontend/src/__tests__/e2eUserJourneys.test.ts` implements a full 12-step end-to-end journey simulating real-world user interaction:

| Step | User Action | Test Assertion & Verification |
|---|---|---|
| **Step 1** | **Initial Dashboard Load** | Verifies default city ("Delhi") loads current AQI, dominant pollutant, category badge, and monitoring station metadata. |
| **Step 2** | **City Selection & Switching** | Changes city to "Mumbai"; verifies state transitions cleanly and retrieves Mumbai-specific stations and AQI values. |
| **Step 3** | **Real-Time Pollutant Breakdown** | Verifies concentrations for $PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3$ with proper units ($\mu g/m^3$, $mg/m^3$). |
| **Step 4** | **Health Advisory & Vulnerable Groups** | Validates structured health recommendations tailored to children, elderly, and outdoor exercisers. |
| **Step 5** | **Historical Analytics & Trends** | Queries 7-day historical trends; verifies time-series point count and data integrity for chart rendering. |
| **Step 6** | **24-Hour Forecast Trajectory** | Inspects upcoming 24-hour predictive curve, ensuring timestamps are strictly in the future. |
| **Step 7** | **AI Health Consultation** | Sends conversational query ("Can I go jogging this evening?"); verifies AI generates contextualized advice with medical disclaimers. |
| **Step 8** | **Alert Configuration** | Configures user notification threshold (e.g., AQI > 200, ); verifies preference persistence. |
| **Step 9** | **Notification Feed & Read Mutations** | Queries user's alert inbox, identifies unread alerts, executes "mark as read", and verifies read status updates. |
| **Step 10** | **Multi-City Comparison** | Compares Delhi vs. Mumbai vs. Bengaluru side-by-side; verifies metrics align without state cross-contamination. |
| **Step 11** | **Network Resilience & Fallback** | Simulates backend 500 error or network disconnection; verifies frontend gracefully transitions to fallback mode without crashing. |
| **Step 12** | **Security & User Context Isolation** | Confirms user alert preferences for User A (`user_alpha`) do not leak or overwrite preferences for User B (`user_beta`). |

---

## 6. How to Run Tests

### 6.1 Complete Verification (All Checks)
To run all tests, linter, production build, and security scans in sequence:

```bash
# From repository root:
(cd frontend && npm test -- --run && npm run lint && npm run build) && \
(cd backend && .venv/bin/pytest && bandit -r app/ -ll && pip-audit)
```

### 6.2 Backend Tests Only
```bash
cd backend
# Run all tests
.venv/bin/pytest

# Run tests with verbose output
.venv/bin/pytest -v

# Run only security tests
.venv/bin/pytest tests/test_security.py -v

# Run with test coverage report
.venv/bin/pytest --cov=app tests/
```

### 6.3 Frontend Tests Only
```bash
cd frontend
# Run all tests once
npm test -- --run

# Run tests in watch mode
npm test

# Run ESLint check
npm run lint

# Run production build validation
npm run build
```

### 6.4 Security Audit Tools
```bash
# Python AST security scanner
cd backend
bandit -r app/ -ll

# Python dependency vulnerability audit
pip-audit

# Node.js dependency vulnerability audit
cd ../frontend
npm audit
```

---

## 7. Continuous Integration & Quality Gates

Any Pull Request or commit to the main branch must pass the following quality gates:

1. **Zero Pytest Failures:** 100% of the 153 backend tests must pass.
2. **Zero Vitest Failures:** 100% of the 51 frontend tests must pass.
3. **Zero ESLint Warnings/Errors:** Code must strictly adhere to project linting rules.
4. **Clean TypeScript Build:** `tsc -b` must compile with 0 type errors.
5. **Clean Security AST Scan:** `bandit` must return 0 Medium or High severity issues.
6. **No Known Production CVEs:** Both `pip-audit` and `npm audit` (production dependencies) must report 0 vulnerabilities.

