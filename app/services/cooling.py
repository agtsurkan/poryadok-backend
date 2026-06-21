"""Client cooling — the «душа» of the product (master §6, brief §6).

A client's *last touch* is derived from the touch/history log; their *state*
(active / warm / cold) is computed from how long ago that was. Thresholds are
configurable. The tone is care, not alarm — `warm`/`cold` mean "maybe a warm
touch", never "overdue".
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Document, User


def _as_aware(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def classify_state(last_touch: datetime | None, now: datetime, warm_days: int, cold_days: int) -> str:
    """active (< warm) · warm (< cold) · cold (>= cold, or never touched)."""
    if last_touch is None:
        return "cold"
    days = (now - last_touch).days
    if days < warm_days:
        return "active"
    if days < cold_days:
        return "warm"
    return "cold"


def effective_last_touch(client_data: dict, touch_times: list[datetime]) -> datetime | None:
    """Latest of the client's own `last_touch_at` and any logged touch."""
    candidates = [t for t in touch_times if t is not None]
    own = _as_aware(client_data.get("last_touch_at"))
    if own:
        candidates.append(own)
    return max(candidates) if candidates else None


async def client_cooling(
    session: AsyncSession, user: User, now: datetime | None = None
) -> list[dict]:
    """Per-client cooling: id, name, state, last_touch_at, days_since, next step."""
    settings = get_settings()
    now = now or datetime.now(timezone.utc)

    clients = (
        await session.execute(
            select(Document)
            .where(Document.user_id == user.id, Document.type == "client")
            .order_by(Document.ord)
        )
    ).scalars().all()

    history = (
        await session.execute(
            select(Document).where(Document.user_id == user.id, Document.type == "history")
        )
    ).scalars().all()

    touches_by_ref: dict[str, list[datetime]] = {}
    for h in history:
        subject = (h.data or {}).get("subject")
        when = h.occurred_at or _as_aware((h.data or {}).get("occurred_at"))
        if subject and when:
            touches_by_ref.setdefault(subject, []).append(_as_aware(when))

    rows = []
    for c in clients:
        last_touch = effective_last_touch(c.data or {}, touches_by_ref.get(f"client:{c.ext_id}", []))
        state = classify_state(last_touch, now, settings.cooling_warm_days, settings.cooling_cold_days)
        next_step = ((c.data or {}).get("brief") or {}).get("next") or (c.data or {}).get("next") or ""
        rows.append(
            {
                "id": c.ext_id,
                "name": (c.data or {}).get("name", ""),
                "state": state,
                "last_touch_at": last_touch.isoformat() if last_touch else None,
                "days_since": (now - last_touch).days if last_touch else None,
                "next": next_step,
            }
        )
    return rows


def _care_note(row: dict) -> str:
    if row["state"] == "cold":
        return "Давно без связи — можно тёплое касание, без спешки."
    return "Понемногу остывает — хороший повод написать."


async def warm_touches(session: AsyncSession, user: User, now: datetime | None = None) -> list[dict]:
    """Clients that could use a touch (warm or cold), most-drifted first."""
    rows = [r for r in await client_cooling(session, user, now) if r["state"] in ("warm", "cold")]
    rows.sort(key=lambda r: (r["days_since"] if r["days_since"] is not None else 10**9), reverse=True)
    for r in rows:
        r["suggestion"] = (f"Написать «{r['name']}»: {r['next']}".strip().rstrip(":")) or r["name"]
        r["note"] = _care_note(r)
    return rows


async def recompute_and_persist(session: AsyncSession, user: User, now: datetime | None = None) -> int:
    """Write computed `state` + `last_touch_at` back onto client docs (the job).

    Computation only — no notifications. Returns the number of clients updated.
    """
    now = now or datetime.now(timezone.utc)
    cooling = {r["id"]: r for r in await client_cooling(session, user, now)}
    clients = (
        await session.execute(
            select(Document).where(Document.user_id == user.id, Document.type == "client")
        )
    ).scalars().all()
    updated = 0
    for c in clients:
        r = cooling.get(c.ext_id)
        if not r:
            continue
        lt = _as_aware(r["last_touch_at"])
        data = dict(c.data or {})
        if data.get("state") != r["state"]:
            data["state"] = r["state"]
            c.data = data
            updated += 1
        c.last_touch_at = lt
        session.add(c)
    return updated
