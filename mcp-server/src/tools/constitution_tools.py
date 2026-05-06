import re
from src.loaders.base_loader import BaseLoader
from src.models.constitution import ConstitutionContent

_VERSION_RE = re.compile(r"version:\s*(.+?)(?:\s*\||\s*$)", re.MULTILINE)


def _domain_path(domain: str) -> str:
    if domain == "global":
        return "constitution.md"
    return f"constitutions/{domain}.md"


def list_constitution_domains(loader: BaseLoader) -> list[str]:
    domains = []
    try:
        loader.read("constitution.md")
        domains.append("global")
    except FileNotFoundError:
        pass
    for path in loader.list("constitutions"):
        if path.endswith(".md"):
            name = path.split("/")[-1].removesuffix(".md")
            domains.append(name)
    return sorted(domains)


def get_constitution(loader: BaseLoader, domain: str = "global") -> ConstitutionContent:
    path = _domain_path(domain)
    content = loader.read(path)
    version_m = _VERSION_RE.search(content)
    version = version_m.group(1).strip() if version_m else ""
    return ConstitutionContent(domain=domain, content=content, version=version, source_path=path)
