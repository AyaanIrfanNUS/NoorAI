"""
Shared pytest fixtures for backend tests.

Tests run against a separate test database so they never touch
development data.
"""

import uuid

import pytest_asyncio
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://noorai_user:noorai_pass@localhost:5432/noorai_test_db"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def redis_test_client():
    test_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    yield test_redis

    await test_redis.flushdb()
    await test_redis.aclose()


@pytest_asyncio.fixture
async def client(db_session, redis_test_client):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    import app.api.auth as auth_module
    original_redis_client = auth_module.redis_client
    auth_module.redis_client = redis_test_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    auth_module.redis_client = original_redis_client


@pytest_asyncio.fixture
def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"