"""Database health verification and connection diagnostics."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger("app.db.init_db")


def check_database_health(db: Session | None = None) -> dict[str, Any]:
    """Verify database connectivity and basic query execution safely."""
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        result = db.execute(text("SELECT 1")).scalar()
        is_healthy = result == 1
        return {
            "status": "connected" if is_healthy else "degraded",
            "healthy": is_healthy,
        }
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        return {
            "status": "disconnected",
            "healthy": False,
        }
    finally:
        if owns_session:
            db.close()

