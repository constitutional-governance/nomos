import re
from src.models.validation import ValidationResult
from src.models.config import ServiceConfig
from src.validators.rollout import apply_rollout


def validate_service_name(name: str, config: ServiceConfig, *, team: str | None = None) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if len(name) > config.max_length:
        errors.append(f"name length {len(name)} exceeds maximum {config.max_length} characters (k8s DNS label limit)")

    if name != name.lower():
        errors.append("service name must be lowercase")

    if name.startswith("-") or name.endswith("-"):
        errors.append("service name must not start or end with a hyphen")

    if "__" in name or "_" in name:
        errors.append("service name must use hyphens, not underscores")

    if "--" in name:
        errors.append("consecutive hyphens are not allowed")

    if not re.match(config.name_pattern, name):
        errors.append(
            f"name '{name}' does not match required pattern '{config.name_pattern}'"
        )

    if name.count("-") == 0:
        warnings.append("single-segment name — consider '{domain}-{system}' pattern for clarity")

    return apply_rollout(
        ValidationResult(valid=not errors, errors=errors, warnings=warnings),
        config.rollout,
        team,
    )
