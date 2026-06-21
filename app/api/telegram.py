"""Telegram webhook (brief §7, P2): capture → show back → confirm → write.

A message (text or voice) is transcribed if needed, routed by Claude into a draft,
and shown back with Confirm / Cancel buttons. Nothing is written until the user
confirms. Whitelisted users only. The endpoint is guarded — 503 until configured.

External I/O (Telegram, Whisper, Claude) means this path is exercised live, not in
the test suite; the routing/draft/write logic underneath it is unit-tested.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_by_email
from app.config import get_settings
from app.db import SessionLocal
from app.models import PendingCapture, User
from app.services.capture import build_index, commit_draft, confirmation_text, draft_from_route
from app.services.llm import route_capture
from app.services.transcribe import transcribe

router = APIRouter(prefix="/telegram", tags=["telegram"])
log = logging.getLogger("poryadok.telegram")
settings = get_settings()


# ──────────────────────────── Telegram helpers ───────────────────────────────
async def _tg(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    import httpx

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    async with httpx.AsyncClient(timeout=20) as client:
        return (await client.post(url, json=payload)).json()


async def _tg_download(file_id: str) -> tuple[bytes, str]:
    import httpx

    info = await _tg("getFile", {"file_id": file_id})
    path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
    return resp.content, path.rsplit("/", 1)[-1]


def _keyboard(pid: uuid.UUID) -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {"text": "✅ Подтвердить", "callback_data": f"ok:{pid}"},
            {"text": "✖️ Отменить", "callback_data": f"no:{pid}"},
        ]]
    }


def _allowed(tg_user_id: int) -> bool:
    ids = settings.allowed_telegram_ids
    return not ids or tg_user_id in ids  # empty whitelist = allow (dev)


# ──────────────────────────────── webhook ────────────────────────────────────
@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, Any]:
    if not settings.telegram_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram not configured")
    # The secret token is the trust boundary that proves an update really came
    # from Telegram. Require it whenever the bot is enabled — never fail open:
    # an unset secret refuses to serve rather than accepting any caller.
    if not settings.telegram_webhook_secret:
        log.error("TELEGRAM_WEBHOOK_SECRET is unset; refusing to process webhook updates")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram webhook secret not configured"
        )
    if not x_telegram_bot_api_secret_token or not secrets.compare_digest(
        x_telegram_bot_api_secret_token, settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="bad secret token")

    update = await request.json()
    try:
        async with SessionLocal() as session:
            if "message" in update:
                await _on_message(session, update["message"])
            elif "callback_query" in update:
                await _on_callback(session, update["callback_query"])
            await session.commit()
    except Exception:  # never retry-storm Telegram — log and ack
        log.exception("telegram update handling failed")
    return {"ok": True}


async def _on_message(session: AsyncSession, msg: dict[str, Any]) -> None:
    chat_id = msg["chat"]["id"]
    tg_user_id = msg.get("from", {}).get("id", 0)
    if not _allowed(tg_user_id):
        await _tg("sendMessage", {"chat_id": chat_id, "text": "Доступ только по приглашению."})
        return

    text = msg.get("text")
    if not text and "voice" in msg:
        audio, name = await _tg_download(msg["voice"]["file_id"])
        text = await transcribe(audio, filename=name)
        await _tg("sendMessage", {"chat_id": chat_id, "text": f"Расшифровал: «{text}»"})
    if not text:
        return

    user = await get_user_by_email(session, settings.auth_email)
    if user is None:
        await _tg("sendMessage", {"chat_id": chat_id, "text": "Пользователь не настроен на сервере."})
        return

    index = await build_index(session, user)
    route = await route_capture(text, index)
    draft = draft_from_route(route)

    pending = PendingCapture(user_id=user.id, chat_id=str(chat_id), transcript=text, draft=draft)
    session.add(pending)
    await session.flush()  # assign pending.id
    await _tg("sendMessage", {"chat_id": chat_id, "text": confirmation_text(draft), "reply_markup": _keyboard(pending.id)})


async def _on_callback(session: AsyncSession, cq: dict[str, Any]) -> None:
    tg_user_id = cq.get("from", {}).get("id", 0)
    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    action, _, raw_id = (cq.get("data") or "").partition(":")
    await _tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
    if not _allowed(tg_user_id):
        return
    try:
        pending = await session.get(PendingCapture, uuid.UUID(raw_id))
    except (ValueError, TypeError):
        pending = None
    if pending is None or pending.status != "pending":
        return

    if action == "ok":
        user = await session.get(User, pending.user_id)
        if user is not None:
            await commit_draft(session, user, pending.draft)
            pending.status = "written"
            await _tg("sendMessage", {"chat_id": chat_id, "text": "Записал ✓"})
    else:
        pending.status = "cancelled"
        await _tg("sendMessage", {"chat_id": chat_id, "text": "Отменил."})
    session.add(pending)
