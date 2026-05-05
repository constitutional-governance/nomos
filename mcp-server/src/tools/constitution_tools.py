import re
from src.loaders.base_loader import BaseLoader
from src.models.constitution import ConstitutionContent, ConstitutionDomain

_VERSION_RE = re.compile(r"version:\s*(.+?)(?:\s*\||\s*$)", re.MULTILINE)

_DOMAIN_PATHS: dict[ConstitutionDomain, str] = {
    "global": "constitution.md",
    "kafka": "constitutions/kafka.md",
    "camel": "constitutions/camel.md",
    "springboot": "constitutions/springboot.md",
    "helm": "constitutions/helm.md",
}


def get_constitution(loader: BaseLoader, domain: ConstitutionDomain = "global") -> ConstitutionContent:
    path = _DOMAIN_PATHS[domain]
    content = loader.read(path)
    version_m = _VERSION_RE.search(content)
    version = version_m.group(1).strip() if version_m else ""
    return ConstitutionContent(domain=domain, content=content, version=version, source_path=path)
