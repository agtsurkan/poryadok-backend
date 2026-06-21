"""P2 capture logic: routing → draft → confirm → write (LLM faked, no Telegram)."""

from __future__ import annotations

from sqlalchemy import select

from app.models import Document
from app.schemas import StateBundle
from app.seed_data import demo_bundle
from app.services.bundle import apply_bundle
from app.services.capture import build_index, commit_draft, confirmation_text, draft_from_route
from app.services.llm import route_capture


def test_draft_mapping_task_thought_touch():
    task = draft_from_route(
        {"kind": "task", "text": "Позвонить", "link_type": "client", "link_id": "c2", "due": "today"}
    )
    assert task["entity_type"] == "task"
    assert task["data"]["tag"] == "client" and task["data"]["link"] == {"type": "client", "id": "c2"}
    assert task["data"]["today"] is True

    thought = draft_from_route({"kind": "thought", "text": "Идея", "link_type": None, "link_id": None, "due": None})
    assert thought["entity_type"] == "thought" and thought["data"]["link"] is None

    touch = draft_from_route({"kind": "touch", "text": "Созвон", "link_type": "client", "link_id": "c1", "due": None})
    assert touch["entity_type"] == "history"
    assert touch["data"]["kind"] == "touch" and touch["data"]["subject"] == "client:c1"
    assert "Записать?" in confirmation_text(touch)


class _FakeBlock:
    type = "tool_use"

    def __init__(self, data):
        self.input = data


class _FakeResp:
    def __init__(self, data):
        self.content = [_FakeBlock(data)]


class _FakeMessages:
    def __init__(self, data):
        self._data = data

    async def create(self, **kwargs):
        # the router must force its tool and pass an INDEX
        assert kwargs["tool_choice"]["name"] == "route_capture"
        return _FakeResp(self._data)


class _FakeAnthropic:
    def __init__(self, data):
        self.messages = _FakeMessages(data)


async def test_route_capture_parses_tool_input():
    fake = _FakeAnthropic({"kind": "task", "text": "x", "link_type": None, "link_id": None, "due": None})
    route = await route_capture("позвонить клиенту", index="client:c1 Веб-волна", client=fake)
    assert route["kind"] == "task" and route["text"] == "x"


async def test_build_index_and_commit_draft(session, user):
    await apply_bundle(session, user, StateBundle(**demo_bundle()))
    await session.commit()

    index = await build_index(session, user)
    assert "client:c1" in index and "project:p1" in index

    draft = draft_from_route(
        {"kind": "task", "text": "Из телеграма", "link_type": "project", "link_id": "p1", "due": None}
    )
    await commit_draft(session, user, draft)
    await session.commit()

    saved = (
        await session.execute(
            select(Document).where(
                Document.user_id == user.id, Document.type == "task", Document.ext_id == draft["data"]["id"]
            )
        )
    ).scalar_one()
    assert saved.data["text"] == "Из телеграма"
    assert saved.today is True  # promoted column populated on write


async def test_webhook_guarded_when_unconfigured(client):
    # No TELEGRAM_BOT_TOKEN in the test env → endpoint is unavailable.
    resp = await client.post("/telegram/webhook", json={"update_id": 1})
    assert resp.status_code == 503


async def test_webhook_fails_closed_when_secret_unset(client, monkeypatch):
    """Bot enabled but no webhook secret must refuse to serve, never fail open."""
    from app.api import telegram as tg

    monkeypatch.setattr(tg.settings, "telegram_bot_token", "test-token")
    monkeypatch.setattr(tg.settings, "telegram_webhook_secret", None)
    resp = await client.post("/telegram/webhook", json={"update_id": 1})
    assert resp.status_code == 503  # not 200 — a missing secret closes the door


async def test_webhook_requires_matching_secret(client, monkeypatch):
    from app.api import telegram as tg

    monkeypatch.setattr(tg.settings, "telegram_bot_token", "test-token")
    monkeypatch.setattr(tg.settings, "telegram_webhook_secret", "s3cret")

    # Missing and wrong secret headers are both rejected.
    assert (await client.post("/telegram/webhook", json={"update_id": 1})).status_code == 403
    bad = await client.post(
        "/telegram/webhook", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": "nope"}
    )
    assert bad.status_code == 403

    # Correct secret is accepted (empty update is a harmless no-op).
    ok = await client.post(
        "/telegram/webhook", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"}
    )
    assert ok.status_code == 200
