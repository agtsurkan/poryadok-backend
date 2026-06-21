"""Morning digest (brief §6.3) — a calm summary, never a guilt list.

Today's focus, one or two warm touches, the next events. No counters, no
"overdue". Built on demand so it's always fresh.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, User
from app.services.cooling import warm_touches


async def build_morning_digest(
    session: AsyncSession, user: User, now: datetime | None = None
) -> dict:
    now = now or datetime.now(timezone.utc)

    focus_docs = (
        await session.execute(
            select(Document)
            .where(
                Document.user_id == user.id,
                Document.type == "task",
                Document.today.is_(True),
                or_(Document.done.is_(False), Document.done.is_(None)),
            )
            .order_by(Document.ord)
        )
    ).scalars().all()
    focus = [d.data for d in focus_docs]

    touches = (await warm_touches(session, user, now))[:2]

    event_docs = (
        await session.execute(
            select(Document)
            .where(Document.user_id == user.id, Document.type == "event")
            .order_by(Document.ord)
        )
    ).scalars().all()
    upcoming = sorted(
        (e.data for e in event_docs if (e.data or {}).get("dayRel", 0) >= 0),
        key=lambda d: (d.get("dayRel", 0), d.get("hour", 0)),
    )[:3]

    return {
        "date": now.date().isoformat(),
        "focus": focus,
        "touches": touches,
        "upcoming": upcoming,
        # A gentle one-liner; never a count of debts.
        "greeting": "В делах порядок. Вот что есть на сегодня — без спешки.",
    }
