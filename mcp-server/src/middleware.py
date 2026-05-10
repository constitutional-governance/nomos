import re
from starlette.types import ASGIApp, Receive, Scope, Send
from src.context import _current_team

_TEAM_RE = re.compile(r"^/teams/([^/]+)(/.*)$")


class TeamContextMiddleware:
    """
    Extracts team from URL path /teams/<team>/... and injects it into the
    _current_team contextvar for the duration of the request.

    Rewrites the path by stripping the /teams/<team> prefix so the MCP app
    receives the request at its expected path (e.g. /mcp/...).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            m = _TEAM_RE.match(path)
            if m:
                team, suffix = m.group(1), m.group(2)
                scope = {**scope, "path": suffix, "raw_path": suffix.encode()}
                token = _current_team.set(team)
                try:
                    await self.app(scope, receive, send)
                    return
                finally:
                    _current_team.reset(token)
        await self.app(scope, receive, send)
