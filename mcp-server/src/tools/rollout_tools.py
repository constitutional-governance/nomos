"""get_rollout_status — query the canary rollout phase for a governance rule."""
from src.models.config import GovernanceConfig, RolloutConfig
from src.models.rollout import RolloutStatus

# Supported rule names and how they map to a RolloutConfig (or None).
_RULE_NAMES = {
    "kafka.topic",
    "kafka.rbac",
    "kafka.service_account",
    "kafka.schema_registry",
    "rest_api",
    "service",
}


def _resolve(rule_name: str, config: GovernanceConfig) -> RolloutConfig | None:
    match rule_name:
        case "kafka.topic":
            return config.kafka.topic.rollout
        case "kafka.rbac":
            return config.kafka.rbac.rollout
        case "kafka.service_account":
            return config.kafka.service_account.rollout
        case "kafka.schema_registry":
            return config.kafka.schema_registry.rollout
        case "rest_api":
            return config.rest_api.rollout
        case "service":
            return config.service.rollout
        case _:
            raise ValueError(
                f"unknown rule_name '{rule_name}'. "
                f"Valid names: {', '.join(sorted(_RULE_NAMES))}"
            )


def get_rollout_status(rule_name: str, config: GovernanceConfig) -> RolloutStatus:
    """Return the current rollout phase and canary teams for a governance rule.

    Args:
        rule_name: One of: kafka.topic, kafka.rbac, kafka.service_account,
                   kafka.schema_registry, rest_api, service.
        config:    The active GovernanceConfig (from _config() in server.py).

    Returns:
        RolloutStatus with phase, teams, and enforced_for_all flag.

    Raises:
        ValueError: if rule_name is not recognised.
    """
    rollout = _resolve(rule_name, config)
    if rollout is None or rollout.phase == "stable":
        return RolloutStatus(
            rule_name=rule_name,
            phase="stable",
            teams=[],
            enforced_for_all=True,
        )
    return RolloutStatus(
        rule_name=rule_name,
        phase=rollout.phase,
        teams=list(rollout.teams),
        enforced_for_all=False,
    )
