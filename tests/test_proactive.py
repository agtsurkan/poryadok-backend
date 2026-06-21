"""P1 proactivity: cooling classification, warm-touch suggestions, morning digest."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Document
from app.schemas import StateBundle
from app.seed_data import demo_bundle
from app.services.bundle import apply_bundle
from app.services.cooling import classify_state, recompute_and_persist


def test_classify_state():
    now = datetime(2026, 6, 21, tzinfo=timezone.utc)
    assert classify_state(None, now, 7, 21) == "cold"
    assert classify_state(now - timedelta(days=3), now, 7, 21) == "active"
    assert classify_state(now - timedelta(days=10), now, 7, 21) == "warm"
    assert classify_state(now - timedelta(days=30), now, 7, 21) == "cold"


async def test_warm_touch_suggestions(auth_client):
    await auth_client.put("/state", json=demo_bundle())
    rows = (await auth_client.get("/suggestions/touches")).json()
    # c1 last touch 24d -> cold (most drifted, first); c3 10d -> warm.
    assert [r["id"] for r in rows[:2]] == ["c1", "c3"]
    assert rows[0]["state"] == "cold" and rows[1]["state"] == "warm"
    assert all(r.get("suggestion") and r.get("note") for r in rows)
    # active clients (c2 6d, c4 1d) are not nagged about.
    assert "c2" not in [r["id"] for r in rows]


async def test_morning_digest(auth_client):
    await auth_client.put("/state", json=demo_bundle())
    d = (await auth_client.get("/digest/morning")).json()
    assert {t["id"] for t in d["focus"]} == {"t1", "t2", "t3", "t4"}  # today & not done
    assert len(d["touches"]) <= 2 and d["touches"][0]["id"] == "c1"
    assert [e["id"] for e in d["upcoming"]] == ["ev1", "ev2", "ev3"]
    assert d["greeting"]  # calm, no counters


async def test_recompute_persists_computed_state(session, user):
    await apply_bundle(session, user, StateBundle(**demo_bundle()))
    await session.commit()

    changed = await recompute_and_persist(session, user)
    await session.commit()
    assert changed >= 1  # at least c1 flips (seed 'cold' already, c2/c3 recomputed)

    c2 = await session.scalar(
        select(Document).where(
            Document.user_id == user.id, Document.type == "client", Document.ext_id == "c2"
        )
    )
    assert c2.data["state"] == "active"  # order 6 days ago
    assert c2.last_touch_at is not None
