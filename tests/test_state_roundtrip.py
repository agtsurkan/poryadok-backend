"""`PUT /state` → `GET /state` round-trips the bundle, and partial saves merge
safely (absent entity types are preserved)."""

from __future__ import annotations

from app.seed_data import demo_bundle

ENTITY_KEYS = [
    "tasks", "inbox", "directions", "projects", "clients",
    "events2", "events", "quickLinks", "services", "history", "links",
]


async def test_put_then_get_roundtrips_the_bundle(auth_client):
    bundle = demo_bundle()

    put = await auth_client.put("/state", json=bundle)
    assert put.status_code == 200, put.text

    got = (await auth_client.get("/state")).json()

    # Every collection comes back verbatim, in order.
    for key in ENTITY_KEYS:
        assert got[key] == bundle[key], f"mismatch in {key!r}"

    # Top-level passthrough (ver / seq / hapticOn) is preserved too.
    assert got["ver"] == bundle["ver"]
    assert got["seq"] == bundle["seq"]
    assert got["hapticOn"] == bundle["hapticOn"]

    # PUT returns the same fresh bundle it would GET.
    assert put.json() == got


async def test_get_returns_all_keys_even_when_empty(auth_client):
    got = (await auth_client.get("/state")).json()
    for key in ENTITY_KEYS:
        assert got[key] == []
    assert got["ver"] == 2


async def test_partial_put_preserves_absent_types(auth_client):
    """A partial autosave (the frontend omits projects/clients/directions/history)
    must not wipe what it didn't send."""
    await auth_client.put("/state", json=demo_bundle())

    # Mimic the frontend's partial autosave: only tasks (+ a couple of types).
    await auth_client.put(
        "/state",
        json={
            "ver": 2,
            "tasks": [
                {"id": "t9", "text": "новая", "tag": "note", "effort": 1,
                 "today": True, "done": False, "link": None}
            ],
        },
    )

    got = (await auth_client.get("/state")).json()
    assert [t["id"] for t in got["tasks"]] == ["t9"]  # present type replaced
    assert len(got["clients"]) == 4  # absent type untouched
    assert len(got["projects"]) == 5
    assert len(got["directions"]) == 2
    assert len(got["history"]) == 6
    assert len(got["links"]) == 2


async def test_present_empty_list_clears_that_type(auth_client):
    await auth_client.put("/state", json=demo_bundle())
    await auth_client.put("/state", json={"tasks": []})
    got = (await auth_client.get("/state")).json()
    assert got["tasks"] == []        # explicitly cleared
    assert len(got["clients"]) == 4  # still untouched
