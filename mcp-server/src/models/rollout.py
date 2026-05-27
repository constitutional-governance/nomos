from pydantic import BaseModel


class RolloutStatus(BaseModel):
    """Describes the current rollout phase of a governance rule."""
    rule_name: str
    phase: str          # "stable" | "canary"
    teams: list[str]    # teams under full enforcement; empty when phase is stable
    enforced_for_all: bool  # True when phase is stable
