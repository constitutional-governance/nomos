import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def validate_topic(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import topic as v
    body = await request.json()
    result = v.validate_topic_name(body.get("name", ""), _config().kafka.topic)
    logger.info("REST validate_topic name=%s valid=%s", body.get("name"), result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_rbac(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import rbac as v
    body = await request.json()
    result = v.validate_rbac_binding(
        body.get("role_name", ""),
        body.get("resource_type", ""),
        body.get("resource_name", ""),
        _config().kafka.rbac,
    )
    logger.info("REST validate_rbac role=%s valid=%s", body.get("role_name"), result.valid)
    return JSONResponse(result.model_dump(), status_code=200 if result.valid else 422)


async def validate_sa(request: Request) -> JSONResponse:
    from src.server import _config
    from src.validators import sa_naming as v
    body = await request.json()
    result = v.validate_sa_name(body.get("name", ""), _config().kafka.service_account)
    logger.info("REST validate_sa name=%s valid=%s", body.get("name"), result.valid)
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
    Route("/webhook/github", github_webhook, methods=["POST"]),
]
