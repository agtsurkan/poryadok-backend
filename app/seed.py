"""Seed the demo user and demo data.

Usage (after the schema exists — `alembic upgrade head`):

    python -m app.seed

Idempotent: re-running resets entity data back to the demo bundle and ensures
the single user (AUTH_EMAIL / AUTH_PASSWORD) exists.
"""

from __future__ import annotations

import asyncio

from app.auth import get_user_by_email, hash_password
from app.config import get_settings
from app.db import SessionLocal
from app.models import User
from app.schemas import StateBundle
from app.seed_data import demo_bundle
from app.services.bundle import apply_bundle


async def seed() -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        user = await get_user_by_email(session, settings.auth_email)
        if user is None:
            user = User(
                email=settings.auth_email,
                password_hash=hash_password(settings.auth_password),
                settings={},
            )
            session.add(user)
            await session.flush()  # assign user.id before documents reference it
            print(f"· created user {settings.auth_email}")
        else:
            print(f"· user {settings.auth_email} already exists")

        await apply_bundle(session, user, StateBundle(**demo_bundle()))
        await session.commit()
        print("· demo data loaded")


if __name__ == "__main__":
    asyncio.run(seed())
