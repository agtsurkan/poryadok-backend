"""Translate between the wire `StateBundle` and stored documents/links/settings.

This is the whole of P0's cleverness, kept in one place:

* `apply_bundle`  — PUT: replace each entity type *present* in the payload;
                    leave absent types untouched (safe for partial autosaves).
* `build_bundle`  — GET: reassemble the full bundle, entities echoed verbatim
                    and in their stored order.

The wire keeps the frontend's own key names; here we map them to clean internal
types and back.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ENTITY_TYPES, Document, LinkEdge, User
from app.schemas import StateBundle

# Wire key (frontend's localStorage name) → internal entity type.
WIRE_TO_TYPE: dict[str, str] = {
    "tasks": "task",
    "inbox": "thought",
    "directions": "direction",
    "projects": "project",
    "clients": "client",
    "events2": "event",  # calendar
    "events": "activity",  # activity log
    "quickLinks": "quicklink",
    "services": "service",
    "history": "history",
}
TYPE_TO_WIRE: dict[str, str] = {v: k for k, v in WIRE_TO_TYPE.items()}
WIRE_ENTITY_KEYS = set(WIRE_TO_TYPE)


# ────────────────────────────── helpers ──────────────────────────────────────
def parse_ref(ref: str) -> tuple[str, str]:
    """\"project:p1\" -> (\"project\", \"p1\")."""
    kind, _, ident = str(ref).partition(":")
    return kind, ident


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def promote(entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Extract the indexable columns duplicated out of the JSON (P1 queries)."""
    cols: dict[str, Any] = {}
    if entity_type == "task":
        cols["done"] = bool(data["done"]) if "done" in data else None
        cols["today"] = bool(data["today"]) if "today" in data else None
    elif entity_type == "history":
        cols["occurred_at"] = _parse_dt(data.get("occurred_at"))
        cols["amount"] = data.get("amount")
        cols["subject_ref"] = data.get("subject")
    elif entity_type == "client":
        # P1 will derive this from the touch/history log; keep what's given now.
        cols["last_touch_at"] = _parse_dt(data.get("last_touch_at"))
    return cols


# ─────────────────────────── PUT: apply bundle ───────────────────────────────
async def apply_bundle(session: AsyncSession, user: User, bundle: StateBundle) -> None:
    raw = bundle.model_dump(exclude_unset=True)

    for wire_key, entity_type in WIRE_TO_TYPE.items():
        items = raw.get(wire_key)
        if isinstance(items, list):  # present (even if empty) → replace
            await _replace_entities(session, user, entity_type, items)

    if isinstance(raw.get("links"), list):
        await _replace_links(session, user, raw["links"])

    passthrough = {
        k: v for k, v in raw.items() if k not in WIRE_ENTITY_KEYS and k != "links"
    }
    if passthrough:
        user.settings = {**(user.settings or {}), **passthrough}
        session.add(user)


async def _replace_entities(
    session: AsyncSession, user: User, entity_type: str, items: list[dict[str, Any]]
) -> None:
    await session.execute(
        delete(Document).where(Document.user_id == user.id, Document.type == entity_type)
    )
    for i, data in enumerate(items):
        session.add(
            Document(
                user_id=user.id,
                type=entity_type,
                ext_id=str(data.get("id", i)),
                ord=i,
                data=data,
                **promote(entity_type, data),
            )
        )


async def _replace_links(session: AsyncSession, user: User, items: list[dict[str, Any]]) -> None:
    await session.execute(delete(LinkEdge).where(LinkEdge.user_id == user.id))
    for i, data in enumerate(items):
        a_type, a_id = parse_ref(data["a"])
        b_type, b_id = parse_ref(data["b"])
        session.add(
            LinkEdge(
                user_id=user.id,
                ext_id=str(data.get("id", i)),
                ord=i,
                a_type=a_type,
                a_id=a_id,
                b_type=b_type,
                b_id=b_id,
            )
        )


# ─────────────────────────── GET: build bundle ───────────────────────────────
async def build_bundle(session: AsyncSession, user: User) -> dict[str, Any]:
    docs = (
        await session.execute(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.type, Document.ord)
        )
    ).scalars().all()

    by_type: dict[str, list[dict[str, Any]]] = {t: [] for t in ENTITY_TYPES}
    for doc in docs:
        by_type[doc.type].append(doc.data)

    links = (
        await session.execute(
            select(LinkEdge).where(LinkEdge.user_id == user.id).order_by(LinkEdge.ord)
        )
    ).scalars().all()

    bundle: dict[str, Any] = {}
    bundle.update(user.settings or {})  # ver, seq, hapticOn, settings, …
    bundle["ver"] = bundle.get("ver", 2)
    for entity_type in ENTITY_TYPES:
        bundle[TYPE_TO_WIRE[entity_type]] = by_type[entity_type]
    bundle["links"] = [
        {"id": e.ext_id, "a": f"{e.a_type}:{e.a_id}", "b": f"{e.b_type}:{e.b_id}"} for e in links
    ]
    return bundle
