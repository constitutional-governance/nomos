import re
from src.models.validation import ValidationResult
from src.models.config import SAConfig

_LOWERCASE_HYPHEN = re.compile(r"^[a-z0-9-]+$")


def validate_sa_name(name: str, config: SAConfig) -> ValidationResult:
    """Validate a service account key name (as used in rbac.hcl)."""
    errors: list[str] = []

    if not name.startswith(config.prefix):
        errors.append(f"service account name must start with '{config.prefix}'")

    if name != name.lower():
        errors.append("service account name must be all lowercase")

    if not _LOWERCASE_HYPHEN.match(name):
        errors.append(
            "service account name must contain only lowercase letters, digits, and hyphens"
        )

    parts = name.split("-")
    min_parts = len(config.prefix.rstrip("-").split("-")) + 2  # prefix parts + domain + env

    if len(parts) < min_parts:
        errors.append(
            f"service account name too short; expected at least "
            f"{config.prefix}{{domain}}-{{system}}-{{env}}"
        )
        return ValidationResult(valid=False, errors=errors)

    # Debug SA: ends with {env}-{debug_suffix} — check env is parts[-2]
    if parts[-1] == config.debug_suffix:
        env = parts[-2] if len(parts) >= 2 else ""
        if env not in config.valid_envs:
            errors.append(
                f"debug SA must end with {{env}}-{config.debug_suffix} where env is one of: "
                f"{', '.join(sorted(config.valid_envs))}"
            )
    else:
        # Standard and connector SAs: last part is env
        env = parts[-1]
        if env not in config.valid_envs:
            errors.append(
                f"last segment must be an environment: "
                f"{', '.join(sorted(config.valid_envs))} (got '{env}')"
            )

    # Connector SA: must have connector segment followed by direction
    if "connector" in parts:
        idx = parts.index("connector")
        if idx + 1 >= len(parts):
            errors.append(
                f"connector SA must have a direction segment after 'connector' "
                f"({' or '.join(config.connector_directions)})"
            )
        else:
            direction = parts[idx + 1]
            if direction not in config.connector_directions:
                errors.append(
                    f"connector direction must be one of: "
                    f"{', '.join(config.connector_directions)}, got '{direction}'"
                )

    return ValidationResult(valid=len(errors) == 0, errors=errors)
