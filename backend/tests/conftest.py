"""Pytest configuration and shared test fixtures."""

import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

import sqlite3

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# In-memory SQLite engine using StaticPool so connections share the memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key support on connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=Session,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test in-memory database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide an isolated transactional session for a test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def anyio_backend():
    """Specify asyncio backend for pytest-asyncio and anyio."""
    return "asyncio"


@pytest.fixture
async def client(db_session):
    """Asynchronous HTTP test client with database dependency override."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
