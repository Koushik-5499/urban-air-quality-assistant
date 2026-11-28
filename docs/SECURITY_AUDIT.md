# Security Audit — Urban Air Quality Assistant

**Last Updated:** 2026-11-28  
**Auditor:** Automated Security Review + Manual Code Inspection  
**Scope:** FastAPI backend (Python 3.12) + React/Vite frontend (TypeScript)

## Summary

| Control | Status | Detail |
|---|---|---|
| Scoped Admin RBAC | ✅ Implemented | `ALERT_ADMIN_SECRET`, `SYNC_ADMIN_SECRET`, `FORECAST_ADMIN_SECRET` with `require_admin_scope()` |
| Rate Limiting | ✅ Implemented | `InMemoryRateLimiter` ABC subclass, 429 with `Retry-After` header |
| Body Size Cap | ✅ Implemented | `RequestSizeLimitMiddleware` stream-bounded DoS guard (1 MB default) |
| LLM Prompt Injection | ✅ Implemented | `safety_validator.py` OWASP LLM01 control-char + injection pattern validation |
| CORS Explicit Allowlist | ✅ Implemented | Explicit origin list (not `*`), `Content-Type`, `Authorization`, `X-API-Key` headers |
| Strict CSP | ✅ Implemented | No `unsafe-inline`, externalized `theme-init.js`, nonces removed; CSP in `vercel.json` |
| Cross-Origin Isolation | ✅ Implemented | `COOP: same-origin`, `CORP: same-origin`, `Permissions-Policy: bluetooth=()` |
| Request Traceability | ✅ Implemented | `X-Request-ID` header on all responses |
| Constant-Time Secret Comparison | ✅ Implemented | `hmac.compare_digest()` in `require_admin_scope()` |
| No Secrets in Logs | ✅ Implemented | Pydantic v2 validation error ctx sanitization; no secret values logged |
| Dependency Scanning | ✅ Implemented | `dependabot.yml` weekly pip+npm; `pip-audit` + `npm audit` in CI |
| Bandit Static Analysis | ✅ Clean | Zero medium/high findings — `bandit -q -r app -ll` |
| Input Validation | ✅ Implemented | Pydantic v2 strict models on all endpoints |

## 1. Scoped Admin RBAC

Admin endpoints (`/api/v1/alerts/sync`, `/api/v1/forecasts/trigger`, etc.) require a scoped secret:
- `ALERT_ADMIN_SECRET` for alert management  
- `SYNC_ADMIN_SECRET` for data synchronisation  
- `FORECAST_ADMIN_SECRET` for forecast triggering  
- Verified via `require_admin_scope(scope: AdminScope)` dependency using `hmac.compare_digest()` for constant-time comparison

## 2. LLM Prompt Injection Guard (OWASP LLM01)

`backend/app/services/health/safety_validator.py` validates all AI inputs:
- Strips/rejects control characters  
- Pattern-matches known injection phrases  
- Returns HTTP 400 with generic error (no prompt details leaked)

## 3. Stream-Bounded DoS Guard

`RequestSizeLimitMiddleware` in `backend/app/middleware/` reads chunked request bodies with a configurable byte cap (default 1 MB). Oversized requests return HTTP 413.

## 4. Content Security Policy

`vercel.json` sets strict headers:
- No `unsafe-inline` for scripts  
- Externalized theme initialisation to `public/theme-init.js`  
- `frame-ancestors 'none'` to prevent clickjacking  

## 5. CORS Configuration

Explicit origin allowlist in `backend/app/main.py`:  
- Allowed headers: `Content-Type`, `Authorization`, `X-API-Key`, `X-Admin-Secret`, `X-User-Id`, `X-Request-ID`  
- No wildcard origins in production

## 6. Dependency Vulnerability Scanning

- `pip-audit` runs in CI against `requirements.txt` and `requirements-dev.txt`  
- `npm audit --audit-level=high` runs in frontend CI job  
- `dependabot.yml` triggers weekly automated PRs for both ecosystems

## 7. Known Limitations

- Rate limiting is in-memory (not distributed); for multi-instance deployments, use Redis-backed limiter  
- API keys are environment variables; use a secrets manager (e.g. Vault, GCP Secret Manager) in production  
- AQI data is simulated; production deployment would require verified sensor feeds with data integrity checks

## 8. Route-Level Control Matrix & Automated CI Security Gates

| Control Surface | Route / Scope | Enforcement Mechanism |
| :--- | :--- | :--- |
| Scoped Admin RBAC | `POST /api/v1/alerts/process`, `/alerts/test-notification`, `/forecast/generate`, `/aqi/process`, `/air-quality/sync` | `require_admin_scope("alert" \| "forecast" \| "sync")` with `hmac.compare_digest`; fails closed in staging/production when unset |
| Retired Personal Mutations | `PATCH /alerts/{id}/read`, `/read-all`, `PUT /alerts/preferences`, `POST /alerts/push/subscribe` | Explicitly retired with HTTP `410 Gone` |
| AI Health Route Guard | `POST /api/v1/health/ask` | Optional `AI_ACCESS_SECRET` (`require_ai_access` via `X-AI-Secret`, constant-time `hmac.compare_digest` when configured) + OWASP LLM01 `HealthSafetyValidator` + 500-char max query |
| Rate Limiting | All routes (`20/min` on `/health/ask`; `10/min` on all 5 admin/state-changing routes; `120/min` default) | `RateLimitMiddleware` sliding window with `Retry-After` and `X-RateLimit-Remaining` headers |
| Body-Size Cap | All HTTP endpoints | `RequestSizeLimitMiddleware` enforcing 1 MB (`1,048,576` bytes) via `Content-Length` and streaming chunk count |
| CORS Allowlist & Log Scrubbing | Global middleware & logger | Explicit `CORS_ORIGINS`, methods, and headers (`X-AI-Secret`, `X-Admin-Secret`, `X-API-Key`, `Authorization`); `SecretRedactionFilter` masks Gemini keys, Bearer tokens, and secret key-value pairs |
| Automated CI Security Audits | `.github/workflows/ci.yml` | Static analysis (`bandit -q -r app -ll`), Python CVE audit (`pip-audit -r requirements.txt -r requirements-dev.txt`), and frontend production dependency audit (`npm audit --omit=dev --audit-level=high`) |
