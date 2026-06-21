"""P1 per-entity CRUD + links."""

from __future__ import annotations


async def test_task_crud_lifecycle(auth_client):
    created = await auth_client.post(
        "/tasks",
        json={"text": "новая", "tag": "note", "effort": 1, "today": True, "done": False, "link": None},
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    assert tid

    listed = (await auth_client.get("/tasks")).json()
    assert any(t["id"] == tid for t in listed)

    patched = await auth_client.patch(f"/tasks/{tid}", json={"done": True})
    assert patched.status_code == 200 and patched.json()["done"] is True

    assert (await auth_client.delete(f"/tasks/{tid}")).status_code == 204
    listed = (await auth_client.get("/tasks")).json()
    assert not any(t["id"] == tid for t in listed)


async def test_create_accepts_client_id_and_rejects_duplicate(auth_client):
    r1 = await auth_client.post("/thoughts", json={"id": "my1", "text": "мысль", "kind": "note"})
    assert r1.status_code == 201 and r1.json()["id"] == "my1"
    r2 = await auth_client.post("/thoughts", json={"id": "my1", "text": "dup"})
    assert r2.status_code == 409


async def test_patch_missing_is_404(auth_client):
    assert (await auth_client.patch("/clients/nope", json={"name": "x"})).status_code == 404


async def test_links_crud(auth_client):
    created = await auth_client.post("/links", json={"a": "project:p1", "b": "client:c2"})
    assert created.status_code == 201
    lid = created.json()["id"]

    links = (await auth_client.get("/links")).json()
    assert any(e["id"] == lid and e["a"] == "project:p1" and e["b"] == "client:c2" for e in links)

    assert (await auth_client.delete(f"/links/{lid}")).status_code == 204


async def test_entities_require_auth(client):
    assert (await client.get("/tasks")).status_code in (401, 403)
    assert (await client.post("/tasks", json={"text": "x"})).status_code in (401, 403)
    assert (await client.get("/suggestions/touches")).status_code in (401, 403)
    assert (await client.get("/digest/morning")).status_code in (401, 403)
