"""Database health verification and connection diagnostics."""

from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.logging import get_logger

logger = get_logger("app.db.init_db")


def check_database_health(db: Optional[Session] = None) -> Dict[str, Any]:
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

