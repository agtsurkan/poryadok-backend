"""Per-entity CRUD (brief §4, P1).

Thin REST over the `documents`/`links` tables, kept DRY via one factory that
registers list/create/patch/delete for each collection. Entities stay open
dicts (echoed verbatim); promoted columns are refreshed on write. The server
owns canonical ids but accepts client-supplied ids (offline capture).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_user
from app.db import get_session
from app.models import Document, LinkEdge, User
from app.services.bundle import parse_ref, promote

router = APIRouter(tags=["entities"])

# wire plural -> internal type
COLLECTIONS = {
    "tasks": "task",
    "thoughts": "thought",
    "projects": "project",
    "clients": "client",
    "directions": "direction",
    "events": "event",
    "quicklinks": "quicklink",
    "services": "service",
    "history": "history",
}


async def _ord_for_new(session: AsyncSession, user: User, entity_type: str) -> int:
    n = await session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.user_id == user.id, Document.type == entity_type)
    )
    return int(n or 0)


async def _get_doc(session: AsyncSession, user: User, entity_type: str, item_id: str) -> Document:
    doc = await session.scalar(
        select(Document).where(
            Document.user_id == user.id, Document.type == entity_type, Document.ext_id == item_id
        )
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return doc


def _register(plural: str, entity_type: str) -> None:
    @router.get(f"/{plural}", name=f"{plural}_list")
    async def list_items(
        user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
    ) -> list[dict[str, Any]]:
        docs = (
            await session.execute(
                select(Document)
                .where(Document.user_id == user.id, Document.type == entity_type)
                .order_by(Document.ord)
            )
        ).scalars().all()
        return [d.data for d in docs]

    @router.post(f"/{plural}", status_code=status.HTTP_201_CREATED, name=f"{plural}_create")
    async def create_item(
        payload: dict[str, Any],
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        data = dict(payload)
        item_id = str(data.get("id") or "").strip() or uuid.uuid4().hex[:10]
        data["id"] = item_id
        exists = await session.scalar(
            select(Document.id).where(
                Document.user_id == user.id,
                Document.type == entity_type,
                Document.ext_id == item_id,
            )
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="id already exists")
        doc = Document(
            user_id=user.id,
            type=entity_type,
            ext_id=item_id,
            ord=await _ord_for_new(session, user, entity_type),
            data=data,
            **promote(entity_type, data),
        )
        session.add(doc)
        await session.commit()
        return data

    @router.patch(f"/{plural}/{{item_id}}", name=f"{plural}_patch")
    async def patch_item(
        item_id: str,
        payload: dict[str, Any],
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        doc = await _get_doc(session, user, entity_type, item_id)
        merged = {**(doc.data or {}), **payload, "id": item_id}
        doc.data = merged
        for col, val in promote(entity_type, merged).items():
            setattr(doc, col, val)
        session.add(doc)
        await session.commit()
        return merged

    @router.delete(f"/{plural}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT, name=f"{plural}_delete")
    async def delete_item(
        item_id: str,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_session),
    ) -> None:
        doc = await _get_doc(session, user, entity_type, item_id)
        await session.delete(doc)
        await session.commit()


for _plural, _type in COLLECTIONS.items():
    _register(_plural, _type)


# ── Links (the relation graph) ────────────────────────────────────────────────
@router.get("/links", name="links_list")
async def list_links(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> list[dict[str, Any]]:
    edges = (
        await session.execute(
            select(LinkEdge).where(LinkEdge.user_id == user.id).order_by(LinkEdge.ord)
        )
    ).scalars().all()
    return [{"id": e.ext_id, "a": f"{e.a_type}:{e.a_id}", "b": f"{e.b_type}:{e.b_id}"} for e in edges]


@router.post("/links", status_code=status.HTTP_201_CREATED, name="links_create")
async def create_link(
    payload: dict[str, Any],
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if "a" not in payload or "b" not in payload:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="a and b required")
    item_id = str(payload.get("id") or "").strip() or uuid.uuid4().hex[:10]
    a_type, a_id = parse_ref(payload["a"])
    b_type, b_id = parse_ref(payload["b"])
    n = await session.scalar(
        select(func.count()).select_from(LinkEdge).where(LinkEdge.user_id == user.id)
    )
    session.add(
        LinkEdge(
            user_id=user.id, ext_id=item_id, ord=int(n or 0),
            a_type=a_type, a_id=a_id, b_type=b_type, b_id=b_id,
        )
    )
    await session.commit()
    return {"id": item_id, "a": payload["a"], "b": payload["b"]}


@router.delete("/links/{item_id}", status_code=status.HTTP_204_NO_CONTENT, name="links_delete")
async def delete_link(
    item_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    edge = await session.scalar(
        select(LinkEdge).where(LinkEdge.user_id == user.id, LinkEdge.ext_id == item_id)
    )
    if edge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await session.delete(edge)
    await session.commit()
