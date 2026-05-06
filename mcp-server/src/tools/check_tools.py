from src.loaders.base_loader import BaseLoader
from src.models.check import Check

_FEATURES_DIR = "mcp-server/features"


def list_check_domains(loader: BaseLoader) -> list[str]:
    paths = loader.list(_FEATURES_DIR)
    domains = set()
    for p in paths:
        parts = p.split("/")
        # mcp-server/features/{domain}/something.feature
        if len(parts) >= 3 and parts[2] != "steps" and p.endswith(".feature"):
            domains.add(parts[2])
    return sorted(domains)


def get_checks(loader: BaseLoader, domain: str) -> list[Check]:
    base_dir = f"{_FEATURES_DIR}/{domain}"
    paths = [p for p in loader.list(base_dir) if p.endswith(".feature")]
    checks = []
    for path in sorted(paths):
        content = loader.read(path)
        title = _extract_title(content)
        status = "enforced" if "@enforced" in content else "draft"
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
