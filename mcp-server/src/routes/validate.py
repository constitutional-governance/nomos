import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


def _team(body: dict) -> str | None:
    """Resolve team from request body, falling back to URL-routed team context."""
    from src.context import _current_team
    return body.get("team") or _current_team.get()


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def validate_topic(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import topic as v
    body = await request.json()
    team = _team(body)
    result = v.validate_topic_name(body.get("name", ""), _config().kafka.topic, team=team)
    logger.info("REST validate_topic name=%s team=%s valid=%s", body.get("name"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_rbac(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import rbac as v
    body = await request.json()
    team = _team(body)
    result = v.validate_rbac_binding(
        body.get("role_name", ""),
        body.get("resource_type", ""),
        body.get("resource_name", ""),
        _config().kafka.rbac,
        team=team,
    )
    logger.info("REST validate_rbac role=%s team=%s valid=%s", body.get("role_name"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_sa(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import sa_naming as v
    body = await request.json()
    team = _team(body)
    result = v.validate_sa_name(body.get("name", ""), _config().kafka.service_account, team=team)
    logger.info("REST validate_sa name=%s team=%s valid=%s", body.get("name"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_schema(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import schema as v
    body = await request.json()
    team = _team(body)
    result = v.validate_schema_entry(
        body.get("format", ""),
        body.get("compatibility_level", ""),
        _config().kafka.schema_registry,
        team=team,
    )
    logger.info("REST validate_schema format=%s team=%s valid=%s", body.get("format"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_rest_path(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import rest_path as v
    body = await request.json()
    team = _team(body)
    result = v.validate_rest_path(body.get("path", ""), _config().rest_api, team=team)
    logger.info("REST validate_rest_path path=%s team=%s valid=%s", body.get("path"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_service_name(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import service_name as v
    body = await request.json()
    team = _team(body)
    result = v.validate_service_name(body.get("name", ""), _config().service, team=team)
    logger.info("REST validate_service_name name=%s team=%s valid=%s", body.get("name"), team, result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def github_webhook(request: Request) -> JSONResponse:
    import src.server as server_module
    loader = server_module._loader()
    if hasattr(loader, "invalidate"):
        loader.invalidate()
    server_module._governance_config = None
    logger.info("cache invalidated via GitHub webhook")
    return JSONResponse({"status": "ok"})


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/validate/topic", validate_topic, methods=["POST"]),
    Route("/validate/rbac", validate_rbac, methods=["POST"]),
    Route("/validate/sa", validate_sa, methods=["POST"]),
    Route("/validate/schema", validate_schema, methods=["POST"]),
    Route("/validate/rest-path", validate_rest_path, methods=["POST"]),
    Route("/validate/service-name", validate_service_name, methods=["POST"]),
    Route("/webhook/github", github_webhook, methods=["POST"]),
]
