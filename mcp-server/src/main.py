import logging
import sys
from src.config import settings
from src.server import mcp

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from src.routes.validate import routes as rest_routes

    mcp_app = mcp.streamable_http_app()

    app = Starlette(routes=[
        *rest_routes,
        Mount("/", mcp_app),
    ])

    uvicorn.run(app, host=settings.mcp_server_host, port=settings.mcp_server_port)


if __name__ == "__main__":
    main()
