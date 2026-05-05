from src.loaders.base_loader import BaseLoader
from src.models.check import Check, CheckDomain

_CHECK_DIRS: dict[CheckDomain, str] = {
    "kafka": "mcp-server/features/kafka",
    "camel": "mcp-server/features/camel",
    "springboot": "mcp-server/features/springboot",
    "helm": "mcp-server/features/helm",
}

_DRAFT_DOMAINS = {"camel", "springboot", "helm"}


def get_checks(loader: BaseLoader, domain: CheckDomain) -> list[Check]:
    base_dir = _CHECK_DIRS[domain]
    paths = [p for p in loader.list(base_dir) if p.endswith(".feature")]
    checks = []
    for path in sorted(paths):
        content = loader.read(path)
        title = _extract_title(content)
        status = "draft" if domain in _DRAFT_DOMAINS else "enforced"
        checks.append(Check(
            domain=domain,
            feature_file=path.split("/")[-1],
            title=title,
            status=status,
            content=content,
            source_path=path,
        ))
    return checks


def _extract_title(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("Feature:"):
            return line[len("Feature:"):].strip()
    return ""
