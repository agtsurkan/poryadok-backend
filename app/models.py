"""ORM models.

Design (see brief §5): one `documents` table holds every entity as a JSON blob,
with a few *promoted* columns duplicated out of the JSON for querying (P1).
`links` is a thin edge table for the relation graph. `users` owns everything.

Why one table + JSON: the frontend's data model still evolves and has nested
arrays (roadmap, discussed, access…). JSON storage maps `GET/PUT /state`
one-to-one and lets new entity types (e.g. the money/history log) appear with
no migration. Hot types can be promoted to dedicated tables later via Alembic.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base

# JSONB on Postgres (indexable), plain JSON elsewhere (SQLite) — portable.
JSON_VARIANT = JSON().with_variant(JSONB(), "postgresql")

# Canonical internal entity types. The wire (bundle) uses the frontend's own
# key names; the mapping lives in `services/bundle.py`.
ENTITY_TYPES: tuple[str, ...] = (
    "task",
    "thought",
    "direction",
    "project",
    "client",
    "event",  # calendar event
    "activity",  # activity-log entry
    "quicklink",
    "service",
    "history",  # money / touch log (model laid in now; computed fields are P1)
)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Non-entity bundle passthrough (ver, seq, hapticOn, ui settings, …).
    settings: Mapped[dict] = mapped_column(JSON_VARIANT, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    links: Mapped[list["LinkEdge"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("user_id", "type", "ext_id", name="uq_documents_user_type_ext"),
        Index("ix_documents_user_type", "user_id", "type"),
        Index("ix_documents_user_type_ord", "user_id", "type", "ord"),
        Index("ix_documents_user_last_touch", "user_id", "last_touch_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    # No standalone index: the (user_id, type[, ord]) composites cover it.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32))
    # The entity's own id from the bundle (e.g. "p1", "c2"). Kept stable so refs
    # like "project:p1" keep resolving; the uuid `id` is purely internal.
    ext_id: Mapped[str] = mapped_column(String(128))
    # Position within (user, type), so `GET /state` round-trips array order.
    ord: Mapped[int] = mapped_column(default=0)
    # The full entity, verbatim — the source of truth for round-trips.
    data: Mapped[dict] = mapped_column(JSON_VARIANT)

    # ── Promoted columns (duplicated from `data` at write time, for P1 queries).
    done: Mapped[bool | None] = mapped_column(default=None)
    today: Mapped[bool | None] = mapped_column(default=None)
    last_touch_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), default=None)
    subject_ref: Mapped[str | None] = mapped_column(String(160), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="documents")


class LinkEdge(Base):
    """An undirected «сцепка» between any two entity refs (the relation graph)."""

    __tablename__ = "links"
    __table_args__ = (UniqueConstraint("user_id", "ext_id", name="uq_links_user_ext"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    ext_id: Mapped[str] = mapped_column(String(128))
    ord: Mapped[int] = mapped_column(default=0)
    a_type: Mapped[str] = mapped_column(String(32))
    a_id: Mapped[str] = mapped_column(String(128))
    b_type: Mapped[str] = mapped_column(String(32))
    b_id: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="links")
