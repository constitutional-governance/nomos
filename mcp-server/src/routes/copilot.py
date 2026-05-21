"""
GitHub Copilot Extension agent endpoint.

Implements the Copilot agent protocol (OpenAI-compatible chat completions with SSE).
Developers invoke it with @nomos in any Copilot-enabled client.

Setup: create a GitHub App with Copilot Extension enabled, point the webhook URL at
POST /copilot/agent on this server, and install the app in your organisation.

Docs: https://docs.github.com/en/copilot/building-copilot-extensions
"""
import json
import logging
import re
import uuid
from typing import AsyncIterator

from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)

_HELP = """\
## Nomos — available commands

**Validate**
- `validate topic <name>`
- `validate sa <name>`
- `validate rbac <role> <resource_type> <resource_name>`
- `validate schema <format> <compatibility>`
- `validate rest-path <path>`
- `validate service <name>`

**Rules**
- `get kafka conventions`
- `get rest conventions`
- `get service conventions`
- `get constitution <domain>`
- `get knowledge failures`
- `get knowledge successful`

**ADRs**
- `list adrs`
- `get adr <id>`
- `search adrs <query>`

**Checks**
- `get checks <domain>`
"""


def _ok(name: str, warnings: list[str]) -> str:
    lines = [f"✅ **{name}**"]
    for w in warnings:
        lines.append(f"- warning: {w}")
    return "\n".join(lines)


def _err(name: str, errors: list[str], warnings: list[str]) -> str:
    lines = [f"❌ **{name}**"]
    for e in errors:
        lines.append(f"- {e}")
    for w in warnings:
        lines.append(f"- warning: {w}")
    return "\n".join(lines)


def _fmt_validation(label: str, result) -> str:
    if result.valid:
        return _ok(label, getattr(result, "warnings", []))
    return _err(label, result.errors, getattr(result, "warnings", []))


async def _dispatch(message: str) -> str:
    from src.server import _config, _loader

    msg = message.strip()
    low = msg.lower()

    # validate topic
    m = re.match(r"validate\s+topic\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import topic as v
        cfg = _config()
        if not cfg.kafka:
            return "Kafka is not configured in this governance repo."
        return _fmt_validation(m.group(1), v.validate_topic_name(m.group(1), cfg.kafka.topic))

    # validate sa
    m = re.match(r"validate\s+sa\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import sa_naming as v
        cfg = _config()
        if not cfg.kafka:
            return "Kafka is not configured in this governance repo."
        return _fmt_validation(m.group(1), v.validate_sa_name(m.group(1), cfg.kafka.service_account))

    # validate rbac <role> <resource_type> <resource_name>
    m = re.match(r"validate\s+rbac\s+(\S+)\s+(\S+)\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import rbac as v
        cfg = _config()
        if not cfg.kafka:
            return "Kafka is not configured in this governance repo."
        role, rtype, rname = m.group(1), m.group(2), m.group(3)
        result = v.validate_rbac_binding(role, rtype, rname, cfg.kafka.rbac)
        label = f"`{role}` on `{rtype}/{rname}`"
        return _fmt_validation(label, result)

    # validate schema <format> <compatibility>
    m = re.match(r"validate\s+schema\s+(\S+)\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import schema as v
        cfg = _config()
        if not cfg.kafka:
            return "Kafka is not configured in this governance repo."
        fmt, compat = m.group(1).upper(), m.group(2).upper()
        return _fmt_validation(f"`{fmt}` / `{compat}`", v.validate_schema_entry(fmt, compat, cfg.kafka.schema_registry))

    # validate rest-path
    m = re.match(r"validate\s+rest[-\s]path\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import rest_path as v
        cfg = _config()
        if not cfg.rest_api:
            return "REST API governance is not configured in this governance repo."
        return _fmt_validation(m.group(1), v.validate_rest_path(m.group(1), cfg.rest_api))

    # validate service
    m = re.match(r"validate\s+service(?:\s+name)?\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.validators import service_name as v
        cfg = _config()
        if not cfg.service:
            return "Service governance is not configured in this governance repo."
        return _fmt_validation(m.group(1), v.validate_service_name(m.group(1), cfg.service))

    # get kafka conventions
    if re.search(r"kafka\s+conv", low):
        from src.tools.convention_tools import get_kafka_conventions
        result = get_kafka_conventions(_config())
        return f"## Kafka conventions\n\n```json\n{json.dumps(result.model_dump(), indent=2)}\n```"

    # get rest conventions
    if re.search(r"rest\s+conv", low):
        from src.tools.convention_tools import get_rest_conventions
        result = get_rest_conventions(_config())
        return f"## REST conventions\n\n```json\n{json.dumps(result.model_dump(), indent=2)}\n```"

    # get service conventions
    if re.search(r"service\s+conv", low):
        from src.tools.convention_tools import get_service_conventions
        result = get_service_conventions(_config())
        return f"## Service conventions\n\n```json\n{json.dumps(result.model_dump(), indent=2)}\n```"

    # get constitution <domain>
    m = re.match(r"get\s+constitution\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.tools.constitution_tools import get_constitution
        try:
            result = get_constitution(_loader(), m.group(1))
            return f"## Constitution: {m.group(1)}\n\n{result.content}"
        except FileNotFoundError:
            return f"Constitution '{m.group(1)}' not found in this governance repo."

    # get knowledge
    m = re.match(r"get\s+knowledge\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.tools.knowledge_tools import get_knowledge
        try:
            return get_knowledge(_loader(), m.group(1))
        except FileNotFoundError:
            return f"Knowledge topic '{m.group(1)}' not found."

    # list adrs
    if re.search(r"list\s+adrs?", low):
        from src.tools.adr_tools import list_adrs
        adrs = list_adrs(_loader())
        if not adrs:
            return "No ADRs found in this governance repo."
        lines = ["## ADRs\n"]
        for a in adrs:
            lines.append(f"- **{a.id}** — {a.title} _{a.status}_")
        return "\n".join(lines)

    # get adr <id>
    m = re.match(r"get\s+adr\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.tools.adr_tools import get_adr
        try:
            result = get_adr(_loader(), m.group(1))
            return result.content
        except FileNotFoundError:
            return f"ADR '{m.group(1)}' not found."

    # search adrs <query>
    m = re.match(r"search\s+adrs?\s+(.+)", msg, re.IGNORECASE)
    if m:
        from src.tools.adr_tools import search_adrs
        query = m.group(1).strip()
        results = search_adrs(_loader(), query)
        if not results:
            return f"No ADRs found matching '{query}'."
        lines = [f"## ADRs matching \"{query}\"\n"]
        for a in results:
            lines.append(f"- **{a.id}** — {a.title} _{a.status}_")
        return "\n".join(lines)

    # get checks <domain>
    m = re.match(r"get\s+checks?\s+(\S+)", msg, re.IGNORECASE)
    if m:
        from src.tools.check_tools import get_checks
        domain = m.group(1)
        checks = get_checks(domain, _loader())
        if not checks:
            return f"No checks found for domain '{domain}'."
        lines = [f"## Checks: {domain}\n"]
        for c in checks:
            icon = "✅" if c.status == "enforced" else "🔧"
            lines.append(f"- {icon} {c.title} _{c.status}_")
        return "\n".join(lines)

    return _HELP


async def _sse_stream(text: str) -> AsyncIterator[bytes]:
    event_id = str(uuid.uuid4())
    chunk_size = 80
    for i in range(0, len(text), chunk_size):
        payload = {
            "id": event_id,
            "choices": [{"delta": {"content": text[i:i + chunk_size], "role": "assistant"}, "index": 0}],
        }
        yield f"data: {json.dumps(payload)}\n\n".encode()
    yield b"data: [DONE]\n\n"


async def copilot_agent(request: Request) -> StreamingResponse | JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    messages = body.get("messages", [])
    user_msg = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    logger.info("copilot agent invoked message=%r", user_msg[:120])

    response_text = await _dispatch(user_msg)
    return StreamingResponse(_sse_stream(response_text), media_type="text/event-stream")


routes = [
    Route("/copilot/agent", copilot_agent, methods=["POST"]),
]
