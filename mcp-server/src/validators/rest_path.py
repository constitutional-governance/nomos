import re
from src.models.validation import ValidationResult
from src.models.config import RestApiConfig

_VERSION_RE = re.compile(r"^v\d+$")
_KEBAB_SEGMENT_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_PATH_PARAM_RE = re.compile(r"^\{[a-z][a-zA-Z0-9_]*\}$")


def validate_rest_path(path: str, config: RestApiConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.startswith("/"):
        errors.append("path must start with '/'")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    if len(path) > 1 and path.endswith("/"):
        errors.append("trailing slash is not allowed")

    segments = [s for s in path.split("/") if s]

    static_segments = [s for s in segments if not _PATH_PARAM_RE.match(s)]
    static_path = "/" + "/".join(static_segments)
    if static_path != static_path.lower():
        errors.append("path must be lowercase — use kebab-case for all static segments")

    if not segments:
        return ValidationResult(valid=not errors, errors=errors, warnings=warnings)

    if config.require_version:
        first = segments[0]
        if not _VERSION_RE.match(first):
            errors.append(
                f"first path segment must be a version (e.g. 'v1', 'v2'), got '{first}'"
            )
        resource_segments = segments[1:]
    else:
        resource_segments = segments

    for seg in resource_segments:
        if _PATH_PARAM_RE.match(seg):
            continue
        if not _KEBAB_SEGMENT_RE.match(seg):
            errors.append(
                f"segment '{seg}' must be lowercase kebab-case (no underscores, no uppercase)"
            )
        if seg.endswith("s") is False and not _PATH_PARAM_RE.match(seg):
            warnings.append(
                f"segment '{seg}' looks like a singular noun — REST resource collections should be plural"
            )

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
