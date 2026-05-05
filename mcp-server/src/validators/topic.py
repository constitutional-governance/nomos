import re
from src.models.validation import ValidationResult
from src.models.config import TopicConfig

_VERSION_RE = re.compile(r"^v\d+$")


def validate_topic_name(name: str, config: TopicConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if len(name) > config.max_length:
        errors.append(f"name length {len(name)} exceeds maximum {config.max_length} characters")

    segments = name.split(".")
    if len(segments) != config.segment_count:
        errors.append(
            f"expected {config.segment_count} dot-separated segments, got {len(segments)}"
        )

    if segments:
        prefix = segments[0]
        valid = set(config.prefixes)
        if prefix not in valid:
            errors.append(
                f"invalid prefix '{prefix}'; must be one of: {', '.join(sorted(valid))}"
            )
        if prefix in config.non_production_prefixes:
            warnings.append(
                f"'{prefix}' prefix topics must not exist in production environments"
            )

    if len(segments) >= config.segment_count:
        version = segments[-1]
        if not _VERSION_RE.match(version):
            errors.append(f"last segment must match v[0-9]+ (got '{version}')")

    if name != name.lower():
        errors.append("all segments must be lowercase")

    for i, seg in enumerate(segments):
        if "-" in seg:
            errors.append(f"segment {i + 1} ('{seg}') contains a hyphen — use dots only")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
