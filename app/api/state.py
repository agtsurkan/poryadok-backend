"""State router: `GET /state` and `PUT /state` — the localStorage bridge (P0).

`GET` hydrates the app on load (replaces reading `poryadok.data`).
`PUT` is the debounced save (replaces writing `poryadok.data`). Last-write-wins,
which is fine for one user; an absent entity type is left untouched (see
`services/bundle.apply_bundle`).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_user
from app.db import get_session
from app.models import User
from app.schemas import StateBundle
from app.services.bundle import apply_bundle, build_bundle

router = APIRouter(tags=["state"])


@router.get("/state")
async def get_state(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await build_bundle(session, user)


@router.put("/state")
async def put_state(
    bundle: StateBundle,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    await apply_bundle(session, user, bundle)
    await session.commit()
    return await build_bundle(session, user)
