"""Test fixtures.

The suite runs on an in-memory SQLite database (StaticPool → one shared
connection), so it needs no external services. The app's `get_session`
dependency is overridden to use that test database.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.config import get_settings
from app.db import Base, get_session
from app.main import app
from app.models import User

settings = get_settings()

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def _schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
def _override_session():
    async def _get_session():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def user(session) -> User:
    u = User(
        email=settings.auth_email,
        password_hash=hash_password(settings.auth_password),
        settings={},
    )
    session.add(u)
    await session.commit()
    return u


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, user: User) -> AsyncClient:
    resp = await client.post(
        "/auth/login",
        json={"email": settings.auth_email, "password": settings.auth_password},
    )
    assert resp.status_code == 200, resp.text
    client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    return client
