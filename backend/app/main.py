"""Urban Air Quality Assistant - FastAPI Main Application Entry Point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, redact_secrets, setup_logging
from app.core.security import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.db.init_db import check_database_health
from app.schemas.health import HealthResponse, RootResponse

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager for startup and shutdown events."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting %s v%s in [%s] mode...", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV
    )
    logger.info("Configured CORS origins: %s", settings.CORS_ORIGINS)
    try:
        from app.db.base import Base
        from app.db.seed import seed_cities
        from app.db.session import SessionLocal, engine

        Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            seed_cities(session)
    except Exception as e:
        # Lifespan startup boundary preventing initialization failure from crashing app
        logger.exception("Database startup init/seed note: %s", str(e))
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


def create_application() -> FastAPI:
    """Instantiate and configure the hardened FastAPI application."""
    settings = get_settings()

    # In production, disable interactive documentation to prevent schema disclosure
    docs_url = None if settings.is_production else "/docs"
    redoc_url = None if settings.is_production else "/redoc"
    openapi_url = None if settings.is_production else "/openapi.json"

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Backend REST API for the Urban Air Quality Assistant platform. "
            "Provides endpoints for real-time air quality metrics, pollutant tracking, "
            "geospatial monitoring, AI health guidance, and environmental alerting."
        ),
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # Middleware stack (Starlette wraps in LIFO order: last added runs outermost):
    # 1. Request Body Size Limit (innermost security check, bounded streaming <= 1MB)
    app.add_middleware(RequestSizeLimitMiddleware)

    # 2. Rate Limiting (mitigates brute-force & resource exhaustion; emits 429 + Retry-After)
    app.add_middleware(RateLimitMiddleware, settings=settings)

    # 3. Security Headers (outermost before CORS so 413/429 responses also carry headers)
    app.add_middleware(SecurityHeadersMiddleware, is_production=settings.is_production)

    # 4. Explicit CORS policy (least-privilege allowlists, no credentials)
    cors_origins = (
        [o for o in settings.CORS_ORIGINS if o != "*"]
        if settings.is_production
        else settings.CORS_ORIGINS
    )
    if not cors_origins:
        cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Admin-Secret",
            "X-User-Id",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "Retry-After"],
        max_age=600,
    )

    # Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle standard HTTP exceptions with structured response and secret scrubbing."""
        sanitized_detail = redact_secrets(exc.detail) if isinstance(exc.detail, str) else exc.detail
        logger.warning("HTTP %s on %s: %s", exc.status_code, request.url.path, sanitized_detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": sanitized_detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic request validation errors.

        Pydantic v2 includes the original exception object in ``ctx['error']``
        when a field_validator raises ValueError.  That object is not JSON-
        serializable, so we convert every ctx value to a string here.
        """
        sanitized: list[dict] = []
        for err in exc.errors():
            err_copy = dict(err)
            if "ctx" in err_copy:
                err_copy["ctx"] = {
                    k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in err_copy["ctx"].items()
                }
            sanitized.append(err_copy)
        logger.warning("Validation error on %s: %s", request.url.path, sanitized)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed",
                "errors": sanitized,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled server exceptions safely without leaking stack traces or secrets."""
        logger.exception("Unhandled server error processing %s: %s", request.url.path, str(exc))
        detail = redact_secrets(str(exc)) if settings.is_development else "Internal server error"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": detail},
        )

    # Root endpoint
    @app.get(
        "/",
        response_model=RootResponse,
        summary="Root Welcome Endpoint",
        tags=["System"],
    )
    async def root() -> RootResponse:
        """Welcome endpoint returning API service status and documentation links."""
        return RootResponse(
            message=f"Welcome to {settings.APP_NAME}",
            status="online",
            docs="/docs" if not settings.is_production else None,
            redoc="/redoc" if not settings.is_production else None,
            version=settings.APP_VERSION,
            api_v1_prefix=settings.API_V1_PREFIX,
        )

    # Basic health-check endpoint
    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Basic Health Check",
        tags=["System"],
    )
    async def health() -> HealthResponse:
        """Root health check returning service status, version, DB status, and UTC timestamp."""
        db_health = check_database_health()
        overall_status = "healthy" if db_health["healthy"] else "degraded"
        return HealthResponse(
            status=overall_status,
            version=settings.APP_VERSION,
            service=settings.APP_NAME,
            timestamp=datetime.now(UTC),
            environment=settings.APP_ENV,
            database=db_health["status"],
        )

    # Mount versioned API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
