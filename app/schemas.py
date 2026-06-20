"""Pydantic schemas: auth payloads, the state bundle envelope, and
documentation-grade entity models mirroring brief §3.

The `/state` endpoint deliberately treats entities as open dicts (echoed back
verbatim) so the contract never fights the still-evolving frontend. The typed
entity models below exist for clarity and OpenAPI; every one allows extra fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─────────────────────────── Auth ────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    # Mirror of `access_token`; brief §4 specifies a `{ token }` shape.
    token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Any
    email: EmailStr


# ───────────────────── Entities (documentation-grade, §3) ────────────────────
class _Open(BaseModel):
    """Base that tolerates extra fields, to stay faithful through frontend churn."""

    model_config = ConfigDict(extra="allow")


Link = dict[str, Any] | None  # { type, id } or null


class Task(_Open):
    id: str
    text: str = ""
    tag: Literal["project", "client", "mail", "note"] = "note"
    effort: int = 2
    today: bool = False
    done: bool = False
    due: str | None = None
    link: Link = None


class Thought(_Open):
    id: str
    text: str = ""
    when: str = ""
    kind: Literal["note", "idea"] = "note"
    link: Link = None
    due: str | None = None


class Direction(_Open):
    id: str
    name: str = ""
    color: str = ""
    note: str = ""


class Project(_Open):
    id: str
    name: str = ""
    kind: str = ""
    progress: float = 0.0
    status: Literal["active", "review", "idea"] = "active"
    next: str = ""
    dir: str | None = None
    parent: str | None = None
    contact: dict[str, Any] | None = None


class Client(_Open):
    id: str
    name: str = ""
    kind: str = ""
    initials: str = ""
    last: str = ""
    state: Literal["cold", "warm", "active"] = "active"
    person: str = ""
    role: str = ""
    company: str = ""
    phone: str = ""
    email: str = ""
    city: str = ""
    intentions: str = ""
    portrait: str = ""
    brief: dict[str, Any] = Field(default_factory=dict)
    discussed: list[dict[str, Any]] = Field(default_factory=list)
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    access: list[dict[str, Any]] = Field(default_factory=list)


class CalendarEvent(_Open):
    id: str
    title: str = ""
    dayRel: int = 0
    hour: int = 9
    dur: int = 1
    color: str = ""
    link: Link = None
    note: str | None = None


class ActivityEvent(_Open):
    id: str
    kind: Literal["done", "note", "add", "client", "move"] = "note"
    text: str = ""
    when: str = ""


class QuickLink(_Open):
    id: str
    type: Literal["project", "client", "note", "external"] = "external"
    label: str = ""


class Service(_Open):
    id: str
    name: str = ""
    hint: str = ""
    connected: bool = False


class LinkEdge(_Open):
    id: str
    a: str  # EntityRef, e.g. "project:p1"
    b: str  # EntityRef, e.g. "client:c2"


class HistoryEntry(_Open):
    """Money / touch log (master §8). Model laid in now; LTV/cooling math is P1."""

    id: str
    kind: Literal["touch", "order", "session", "invoice", "note"] = "touch"
    subject: str | None = None  # EntityRef of the client/project it concerns
    amount: float | None = None
    note: str = ""
    occurred_at: datetime | None = None


# ─────────────────────────── State bundle ────────────────────────────────────
class StateBundle(BaseModel):
    """Wire format of `GET/PUT /state`.

    Field names match the frontend's own `localStorage` keys (true drop-in):
    `inbox` = thoughts, `events2` = calendar, `events` = activity log. Internally
    these normalise to clean entity types (see `services/bundle.py`).

    All collections are optional: on `PUT` an *absent* key leaves that entity
    type untouched, while a present key (even `[]`) replaces it. This protects
    data the partial autosave omits (projects/clients/directions/history).
    Extra top-level keys (`seq`, `hapticOn`, …) are preserved as passthrough.
    """

    model_config = ConfigDict(extra="allow")

    ver: int = 2
    tasks: list[dict[str, Any]] | None = None
    inbox: list[dict[str, Any]] | None = None
    directions: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    clients: list[dict[str, Any]] | None = None
    events2: list[dict[str, Any]] | None = None
    events: list[dict[str, Any]] | None = None
    quickLinks: list[dict[str, Any]] | None = None
    services: list[dict[str, Any]] | None = None
    links: list[dict[str, Any]] | None = None
    history: list[dict[str, Any]] | None = None
    settings: dict[str, Any] | None = None
