import contextvars

# Set by TeamContextMiddleware when a request arrives at /teams/<team>/...
# Read by _loader() in server.py to wrap the base loader with TeamAwareLoader.
_current_team: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "nomos_team", default=None
)
