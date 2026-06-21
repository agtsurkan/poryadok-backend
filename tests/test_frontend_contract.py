"""The contract the web client (frontend/web) relies on — the exact shapes its
api.ts and components read. Guards against backend drift silently breaking the UI.
Pure shape checks; runs on the in-memory DB like the rest of the suite."""

from __future__ import annotations

from app.config import get_settings
from app.seed_data import demo_bundle

settings = get_settings()


async def test_login_returns_bearer_token(client, user):
    """api.ts `login()` expects `{ access_token }`."""
    resp = await client.post(
        "/auth/login",
        json={"email": settings.auth_email, "password": settings.auth_password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json().get("access_token")
    assert isinstance(token, str) and token


async def test_state_exposes_keys_the_client_reads(auth_client):
    await auth_client.put("/state", json=demo_bundle())
    state = (await auth_client.get("/state")).json()

    # store.tsx / Home / Inbox iterate these collections.
    for key in ("tasks", "inbox", "events"):
        assert isinstance(state.get(key), list), f"{key!r} must be a list"

    # TodayTasks / Focus read these task fields.
    task = state["tasks"][0]
    for field in ("id", "text", "tag", "effort", "today", "done"):
        assert field in task, f"task missing {field!r}"

    # Inbox reads these thought fields.
    thought = state["inbox"][0]
    for field in ("id", "text", "when", "kind"):
        assert field in thought, f"thought missing {field!r}"


async def test_frontend_partial_autosave_merges(auth_client):
    """The client holds the whole bundle and PUTs it (debounced); a slice that
    omits other types must merge, not wipe — store.tsx relies on this."""
    await auth_client.put("/state", json=demo_bundle())
    await auth_client.put(
        "/state",
        json={
            "tasks": [
                {"id": "tX", "text": "из веба", "tag": "note", "effort": 2,
                 "today": True, "done": False, "link": None}
            ]
        },
    )
    state = (await auth_client.get("/state")).json()
    assert [t["id"] for t in state["tasks"]] == ["tX"]  # present type replaced
    assert len(state["inbox"]) >= 1                      # absent type preserved


async def test_touches_shape_for_warm_card(auth_client):
    """WarmTouch.tsx reads id/name/state/days_since/next on every row."""
    await auth_client.put("/state", json=demo_bundle())
    resp = await auth_client.get("/suggestions/touches")
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert isinstance(rows, list)
    assert rows, "demo data has a cold + warm client, so the card has something to show"
    for row in rows:
        for field in ("id", "name", "state", "days_since", "next"):
            assert field in row, f"touch row missing {field!r}"
