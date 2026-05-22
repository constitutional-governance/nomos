import argparse
import logging
import sys
from pathlib import Path
from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    from src.commands import install_hooks, check_promotion, scaffold

    parser = argparse.ArgumentParser(
        prog="nomos",
        description="Nomos — Constitutional Governance server and tooling",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Register CLI commands
    install_hooks.register(subparsers)
    check_promotion.register(subparsers)
    scaffold.register(subparsers)

    # Server flags (used when no subcommand is given)
    parser.add_argument(
        "--repo",
        type=Path,
        metavar="PATH",
        help="Path to the governance repository (overrides GOVERNANCE_REPO_PATH)",
    )
    parser.add_argument(
        "--github",
        metavar="URL",
        help="GitHub governance repo URL — enables GitHub mode (overrides GOVERNANCE_REPO_URL)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.mcp_server_port,
        help=f"Port to listen on (default: {settings.mcp_server_port})",
    )
    parser.add_argument(
        "--host",
        default=settings.mcp_server_host,
        help=f"Host to bind to (default: {settings.mcp_server_host})",
    )

    args = parser.parse_args()

    # Dispatch to subcommand if one was given
    if args.command:
        sys.exit(args.func(args))

    # Default: start the governance server
    if args.repo:
        settings.governance_repo_path = args.repo.resolve()
        settings.governance_mode = "local"
    if args.github:
        settings.governance_repo_url = args.github
        settings.governance_mode = "github"

    from contextlib import asynccontextmanager
    from src.server import mcp
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from src.routes.validate import routes as rest_routes
    from src.routes.copilot import routes as copilot_routes
    from src.middleware import TeamContextMiddleware

    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app):
        async with mcp_app.router.lifespan_context(app):
            yield

    base_app = Starlette(routes=[*rest_routes, *copilot_routes, Mount("/", mcp_app)], lifespan=lifespan)
    app = TeamContextMiddleware(base_app)

    logging.getLogger(__name__).info(
        "nomos starting — mode=%s host=%s port=%s",
        settings.governance_mode, args.host, args.port,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
