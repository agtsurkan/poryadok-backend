"""Auth protects the state endpoints; login issues a working bearer token."""

from __future__ import annotations

from app.config import get_settings

settings = get_settings()


async def test_state_requires_auth(client):
    # No Authorization header → unauthenticated (HTTPBearer → 403; invalid → 401).
    assert (await client.get("/state")).status_code in (401, 403)
    assert (await client.put("/state", json={"tasks": []})).status_code in (401, 403)


async def test_invalid_token_rejected(client):
    resp = await client.get("/state", headers={"Authorization": "Bearer not.a.real.jwt"})
    assert resp.status_code == 401


async def test_login_wrong_password(client, user):
    resp = await client.post(
        "/auth/login", json={"email": settings.auth_email, "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client, user):
    resp = await client.post(
        "/auth/login", json={"email": "nobody@poryadok.app", "password": settings.auth_password}
    )
    assert resp.status_code == 401


async def test_login_success_and_me(client, user):
    resp = await client.post(
        "/auth/login", json={"email": settings.auth_email, "password": settings.auth_password}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["token"] == body["access_token"]  # brief §4 `{ token }` mirror

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == settings.auth_email


async def test_authed_state_access(auth_client):
    assert (await auth_client.get("/state")).status_code == 200
