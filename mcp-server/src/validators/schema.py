from src.models.validation import ValidationResult
from src.models.config import SchemaConfig
from src.validators.rollout import apply_rollout


def validate_schema_entry(
    format: str,
    compatibility_level: str,
    config: SchemaConfig,
    *,
    team: str | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if format not in config.valid_formats:
        errors.append(
            f"invalid format '{format}'; must be one of: {', '.join(sorted(config.valid_formats))}"
        )

    if compatibility_level not in config.valid_compatibility_levels:
        errors.append(
            f"invalid compatibility_level '{compatibility_level}'; must be one of: "
            f"{', '.join(config.valid_compatibility_levels)}"
        )

    if format == "AVRO" and compatibility_level == "NONE":
        warnings.append(
            "compatibility_level NONE disables schema evolution checks — "
            "prefer BACKWARD or BACKWARD_TRANSITIVE for production AVRO schemas"
        )

    return apply_rollout(
        ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings),
        config.rollout,
        team,
    )
