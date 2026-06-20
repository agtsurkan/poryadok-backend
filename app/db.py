"""Database engine, session factory and the declarative Base.

Async SQLAlchemy 2.0. The same models run on PostgreSQL (prod, asyncpg) and
SQLite (tests / first local run, aiosqlite) — see `JSONB_OR_JSON` in models.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_settings = get_settings()

# `pool_pre_ping` keeps long-lived managed-Postgres connections healthy.
engine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=not _settings.is_sqlite,
    future=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session and always closes it."""
    async with SessionLocal() as session:
        yield session
