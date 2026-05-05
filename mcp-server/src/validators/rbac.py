from src.models.validation import ValidationResult
from src.models.config import RBACConfig


def validate_rbac_binding(
    role_name: str,
    resource_type: str,
    resource_name: str,
    config: RBACConfig,
) -> ValidationResult:
    errors: list[str] = []
    valid_roles = set(config.valid_roles)
    valid_types = set(config.valid_resource_types)
    admin_roles = set(config.admin_roles)
    admin_types = set(config.admin_resource_types)

    if role_name not in valid_roles:
        errors.append(
            f"invalid role_name '{role_name}'; must be one of: {', '.join(sorted(valid_roles))}"
        )

    if resource_type not in valid_types:
        errors.append(
            f"invalid resource_type '{resource_type}'; must be one of: "
            f"{', '.join(sorted(valid_types))}"
        )

    # Admin roles (e.g. DeveloperManage) are only valid on admin resource types (e.g. cluster)
    if role_name in admin_roles and resource_type not in admin_types:
        errors.append(
            f"{role_name} is only valid on resource_type "
            f"'{' or '.join(sorted(admin_types))}', got '{resource_type}'"
        )

    # Admin resource types require the canonical resource name
    if resource_type in admin_types and resource_name != config.cluster_resource_name:
        errors.append(
            f"resource_type '{resource_type}' requires resource_name "
            f"'{config.cluster_resource_name}', got '{resource_name}'"
        )

    return ValidationResult(valid=len(errors) == 0, errors=errors)
