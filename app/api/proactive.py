"""Proactivity router (P1): warm touches and the morning digest."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_user
from app.db import get_session
from app.models import User
from app.services.cooling import warm_touches
from app.services.digest import build_morning_digest

router = APIRouter(tags=["proactive"])


@router.get("/suggestions/touches")
async def suggestions_touches(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Clients that could use a warm touch (feeds the «Тёплое касание» card)."""
    return await warm_touches(session, user)


@router.get("/digest/morning")
async def digest_morning(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await build_morning_digest(session, user)
