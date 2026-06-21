"""Intent routing via Claude (brief §7, P2).

A captured note (text or voice transcript) is classified into a Порядок entity
and where it attaches, using a cheap model with a forced, strict tool call so the
result is structured JSON. The Anthropic client is injectable so tests can pass a
fake without the SDK or an API key.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings

# Forced tool — its input schema *is* the routing result.
ROUTE_TOOL: dict[str, Any] = {
    "name": "route_capture",
    "description": (
        "Classify a captured note into a Порядок item and where it attaches. "
        "kind: 'task' (a to-do), 'thought' (an idea/note for the inbox), or "
        "'touch' (a contact/interaction with a client). Use the INDEX of existing "
        "projects and clients to fill link_type/link_id when the note clearly refers "
        "to one; otherwise leave them null."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["task", "thought", "touch"]},
            "text": {"type": "string", "description": "cleaned-up text of the item"},
            "link_type": {"type": ["string", "null"], "enum": ["project", "client", "direction", None]},
            "link_id": {"type": ["string", "null"], "description": "id from the INDEX, or null"},
            "due": {"type": ["string", "null"], "description": "'today'|'tomorrow'|'week'|ISO date|null"},
        },
        "required": ["kind", "text", "link_type", "link_id", "due"],
        "additionalProperties": False,
    },
}

SYSTEM = (
    "Ты — тихий помощник «Порядок». Разбери захваченную заметку и реши, что это: "
    "задача, мысль или касание клиента, и к какому проекту/клиенту/направлению её "
    "привязать. Опирайся на INDEX существующих сущностей. Не выдумывай привязки — "
    "если непонятно, оставляй null. Верни результат единственным вызовом route_capture."
)


async def route_capture(text: str, index: str = "", client: Any = None) -> dict[str, Any]:
    """Return `{kind, text, link_type, link_id, due}` for a captured note."""
    settings = get_settings()
    if client is None:  # pragma: no cover - exercised only with a real key
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = text if not index else f"{text}\n\nINDEX:\n{index}"
    resp = await client.messages.create(
        model=settings.router_model,
        max_tokens=1024,
        system=SYSTEM,
        tools=[ROUTE_TOOL],
        tool_choice={"type": "tool", "name": "route_capture"},
        messages=[{"role": "user", "content": message}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    raise RuntimeError("router returned no tool_use block")
