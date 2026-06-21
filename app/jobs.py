"""Nightly job (brief §6.4): recompute client cooling for everyone.

Computation only — it refreshes each client's `state`/`last_touch_at`. No
notifications, no spam ("по принципу чайника"). Wired into the app lifespan and
guarded by `scheduler_enabled` so tests never start it.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import User
from app.services.cooling import recompute_and_persist

log = logging.getLogger("poryadok.jobs")


async def recompute_cooling_all_users() -> None:
    async with SessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        total = 0
        for user in users:
            total += await recompute_and_persist(session, user)
        await session.commit()
        log.info("cooling recompute: %d client(s) changed across %d user(s)", total, len(users))


def start_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        recompute_cooling_all_users,
        trigger="cron",
        hour=settings.digest_hour,
        id="recompute_cooling",
        replace_existing=True,
    )
    scheduler.start()
    log.info("scheduler started (recompute at %02d:00 UTC)", settings.digest_hour)
    return scheduler
