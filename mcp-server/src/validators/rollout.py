"""Canary rollout helper for governance validators.

apply_rollout() is the single implementation of the rollout decision:

  stable (or absent)          → enforce for all teams (no change to result)
  canary + team in list       → enforce fully for that team (no change)
  canary + team NOT in list   → downgrade errors to warnings, valid=True
  canary + no team supplied   → treat as "not in list" (advisory warning)
"""
from src.models.config import RolloutConfig
from src.models.validation import ValidationResult


def apply_rollout(
    result: ValidationResult,
    rollout: RolloutConfig | None,
    team: str | None,
) -> ValidationResult:
    """Return result unchanged, or downgrade errors to warnings for non-canary teams.

    Args:
        result:  The raw ValidationResult from the validator.
        rollout: The rollout config embedded in the rule's config object.
                 None or phase=="stable" → enforce for everyone.
        team:    The requesting team identifier, or None when no team is known.

    Returns:
        The original result when enforcement applies.
        A new result with valid=True and errors converted to warnings when
        the rule is in canary and the requesting team is not in the canary list.
    """
    # Nothing to downgrade, or rule is stable — return as-is.
    if not result.errors:
        return result
    if rollout is None or rollout.phase == "stable":
        return result

    # Canary phase: enforce only for listed teams.
    if team is not None and team in rollout.teams:
        return result  # this team IS in the canary — full enforcement

    # Team is not in canary (or unknown) — downgrade to advisory warnings.
    team_label = f"team '{team}'" if team else "your team"
    enforced_for = ", ".join(rollout.teams) if rollout.teams else "none yet"
    canary_note = (
        f"rule is in canary rollout, not yet enforced for {team_label} "
        f"(enforced for: {enforced_for})"
    )
    downgraded = [f"[canary rollout] {e}" for e in result.errors]
    return ValidationResult(
        valid=True,
        errors=[],
        warnings=result.warnings + downgraded + [canary_note],
    )
