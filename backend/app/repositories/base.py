"""Abstract base class for all repository implementations (Dependency Inversion Principle)."""
from abc import ABC, abstractmethod

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class BaseRepository(ABC):
    """Abstract repository interface enforcing the Repository pattern.

    All concrete repositories must extend this class, ensuring a consistent
    interface and enabling mock/test repositories to substitute cleanly
    (Liskov Substitution Principle).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def _probe_db(self) -> bool:
        """Execute a lightweight connectivity probe against the backing store."""
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except (SQLAlchemyError, RuntimeError):
            return False

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the repository's backing store is reachable.

        Concrete repositories delegate to ``_probe_db()`` or supply a store-
        specific readiness check.
        """
