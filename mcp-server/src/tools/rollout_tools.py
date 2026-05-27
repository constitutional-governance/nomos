"""get_rollout_status — query the canary rollout phase for a governance rule.

Rule names are dotted attribute paths into GovernanceConfig, e.g.:
  "kafka.topic"          →  config.kafka.topic.rollout
  "kafka.service_account"→  config.kafka.service_account.rollout
  "rest_api"             →  config.rest_api.rollout

No registration is required when new rules are added.  Any config section
that inherits from RuleConfig (i.e. has a ``rollout`` attribute) is
automatically reachable by its dotted path.
"""
from typing import Any
from src.models.config import GovernanceConfig, RolloutConfig
from src.models.rollout import RolloutStatus

_SENTINEL = object()


def _resolve(rule_name: str, config: GovernanceConfig) -> RolloutConfig | None:
    """Navigate config by dotted path and return the rollout field.

    Raises ValueError for unknown paths or sections without rollout support.
    """
    obj: Any = config
    for part in rule_name.split("."):
        obj = getattr(obj, part, _SENTINEL)
        if obj is _SENTINEL:
            raise ValueError(
                f"unknown rule_name '{rule_name}' — "
                f"'{part}' is not an attribute of {type(obj).__name__}"
            )
    rollout = getattr(obj, "rollout", _SENTINEL)
    if rollout is _SENTINEL:
        raise ValueError(
            f"'{rule_name}' ({type(obj).__name__}) does not support rollout. "
            f"Make its config class inherit from RuleConfig to enable rollout."
        )
    return rollout  # type: ignore[return-value]


def get_rollout_status(rule_name: str, config: GovernanceConfig) -> RolloutStatus:
    """Return the current rollout phase and canary teams for a governance rule.

    Args:
        rule_name: Dotted attribute path into GovernanceConfig, e.g.
                   'kafka.topic', 'kafka.rbac', 'kafka.service_account',
                   'kafka.schema_registry', 'rest_api', 'service'.
                   Any future RuleConfig section is reachable without code changes.
        config:    The active GovernanceConfig (from _config() in server.py).

    Returns:
        RolloutStatus with phase, teams, and enforced_for_all flag.

    Raises:
        ValueError: if the path does not exist or the section lacks rollout support.
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
