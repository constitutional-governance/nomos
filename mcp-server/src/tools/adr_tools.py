import re
from src.loaders.base_loader import BaseLoader
from src.models.adr import ADRContent, ADRSummary

_ADR_DIR = "adrs/global"
_STATUS_RE = re.compile(r"^##\s+Status\s*\n+(.+)", re.MULTILINE)
_VERSION_RE = re.compile(r"^##\s+Version\s*\n+(.+)", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s+ADR-\d+:\s+(.+)", re.MULTILINE)
_ID_RE = re.compile(r"(\d{3})-")


def _parse_summary(path: str, content: str) -> ADRSummary:
    adr_id = _ID_RE.search(path.split("/")[-1])
    id_str = adr_id.group(1) if adr_id else "???"
    title = (_TITLE_RE.search(content) or type("", (), {"group": lambda s, n: path})()).group(1).strip()
    status_m = _STATUS_RE.search(content)
    status = status_m.group(1).strip().split("—")[0].strip() if status_m else "Unknown"
    domain = _infer_domain(content)
    return ADRSummary(id=id_str, title=title, status=status, domain=domain, source_path=path)


def _infer_domain(content: str) -> str:
    lower = content.lower()
    if "camel" in lower[:500]:
        return "Camel"
    if "springboot" in lower[:500] or "spring boot" in lower[:500]:
        return "SpringBoot"
    if "helm" in lower[:500]:
        return "Helm"
    if "terraform" in lower[:500] or "terragrunt" in lower[:500]:
        return "Platform"
    return "Kafka"


def list_adrs(loader: BaseLoader) -> list[ADRSummary]:
    paths = [p for p in loader.list(_ADR_DIR) if p.endswith(".md") and not p.endswith("README.md")]
    summaries = []
    for path in sorted(paths):
        try:
            content = loader.read(path)
            summaries.append(_parse_summary(path, content))
        except FileNotFoundError:
            pass
    return summaries


def get_adr(loader: BaseLoader, adr_id: str) -> ADRContent:
    # Normalise: "001", "ADR-001", "adr-001" → "001"
    normalised = re.sub(r"[^0-9]", "", adr_id).zfill(3)
    paths = loader.list(_ADR_DIR)
    for path in paths:
        if f"{normalised}-" in path.split("/")[-1]:
            content = loader.read(path)
            summary = _parse_summary(path, content)
            version_m = _VERSION_RE.search(content)
            version = version_m.group(1).strip() if version_m else ""
            return ADRContent(**summary.model_dump(), content=content, version=version)
    raise FileNotFoundError(f"ADR {adr_id} not found")


def search_adrs(loader: BaseLoader, query: str) -> list[ADRSummary]:
    terms = query.lower().split()
    results = []
    for summary in list_adrs(loader):
        content = loader.read(summary.source_path).lower()
        if all(t in content or t in summary.title.lower() for t in terms):
            results.append(summary)
    return results
