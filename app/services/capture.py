"""Capture → confirm → write (brief §7, P2).

Turns a routed note into a *draft* (never written until confirmed), renders the
confirmation a user sees, and—only on confirm—writes the entity. Pure functions
plus two DB helpers, so the whole loop is unit-testable without Telegram or an LLM.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, User
from app.services.bundle import promote


def _new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def _link(route: dict[str, Any]) -> dict[str, str] | None:
    lt, li = route.get("link_type"), route.get("link_id")
    return {"type": lt, "id": li} if lt and li else None


def draft_from_route(route: dict[str, Any]) -> dict[str, Any]:
    """Map a routing result to `{entity_type, data, summary}` (nothing written yet)."""
    kind = route.get("kind", "thought")
    text = (route.get("text") or "").strip()
    link = _link(route)
    due = route.get("due")

    if kind == "task":
        tag = link["type"] if link and link["type"] in ("project", "client") else "note"
        data = {
            "id": _new_id("t"), "text": text, "tag": tag, "effort": 2,
            "today": True, "done": False, "link": link, "due": due,
        }
        where = f" → {link['type']}:{link['id']}" if link else ""
        return {"entity_type": "task", "data": data, "summary": f"✅ Задача: «{text}»{where}"}

    if kind == "touch":
        subject = f"{link['type']}:{link['id']}" if link else None
        data = {
            "id": _new_id("h"), "kind": "touch", "subject": subject,
            "amount": None, "note": text, "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        where = f" с {subject}" if subject else ""
        return {"entity_type": "history", "data": data, "summary": f"🤝 Касание{where}: «{text}»"}

    # default: thought
    data = {"id": _new_id("i"), "text": text, "when": "сейчас", "kind": "note", "link": link, "due": due}
    return {"entity_type": "thought", "data": data, "summary": f"💭 Мысль: «{text}»"}


def confirmation_text(draft: dict[str, Any]) -> str:
    return f"{draft['summary']}\n\nЗаписать?"


async def build_index(session: AsyncSession, user: User, limit: int = 60) -> str:
    """Compact list of existing projects/clients/directions for routing context."""
    docs = (
        await session.execute(
            select(Document)
            .where(Document.user_id == user.id, Document.type.in_(("project", "client", "direction")))
            .order_by(Document.type, Document.ord)
            .limit(limit)
        )
    ).scalars().all()
    return "\n".join(f"{d.type}:{d.ext_id} {(d.data or {}).get('name', '')}".strip() for d in docs)


async def commit_draft(session: AsyncSession, user: User, draft: dict[str, Any]) -> dict[str, Any]:
    """Write the drafted entity. Returns the stored entity data."""
    entity_type = draft["entity_type"]
    data = dict(draft["data"])
    n = await session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.user_id == user.id, Document.type == entity_type)
    )
    session.add(
        Document(
            user_id=user.id, type=entity_type, ext_id=str(data["id"]), ord=int(n or 0),
            data=data, **promote(entity_type, data),
        )
    )
    return data
