"""Tests for Canary Rollout pattern.

Covers:
  - apply_rollout() helper — the core decision function
  - Each validator with team/rollout integration
  - get_rollout_status() tool
  - Edge cases: no team, stable phase, no rollout config
"""
import pytest
from src.models.config import (
    RolloutConfig,
    TopicConfig, RBACConfig, SAConfig, SchemaConfig,
    RestApiConfig, ServiceConfig, GovernanceConfig, KafkaConfig,
)
from src.models.validation import ValidationResult
from src.validators.rollout import apply_rollout
from src.validators.topic import validate_topic_name
from src.validators.rbac import validate_rbac_binding
from src.validators.sa_naming import validate_sa_name
from src.validators.schema import validate_schema_entry
from src.validators.rest_path import validate_rest_path
from src.validators.service_name import validate_service_name
from src.tools.rollout_tools import get_rollout_status


# ── apply_rollout helper ───────────────────────────────────────────────────────

class TestApplyRollout:

    def _ok(self) -> ValidationResult:
        return ValidationResult(valid=True, errors=[], warnings=["existing warning"])

    def _fail(self) -> ValidationResult:
        return ValidationResult(valid=False, errors=["rule broken"], warnings=[])

    # No errors — never touches the result regardless of rollout state
    def test_no_errors_returns_unchanged(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._ok(), rollout, team="other")
        assert result.valid
        assert not result.errors

    # stable phase — always enforce
    def test_stable_phase_preserves_errors(self):
        rollout = RolloutConfig(phase="stable")
        result = apply_rollout(self._fail(), rollout, team="payments")
        assert not result.valid
        assert result.errors

    def test_none_rollout_preserves_errors(self):
        result = apply_rollout(self._fail(), None, team="payments")
        assert not result.valid
        assert result.errors

    # canary + team IN list → enforce
    def test_canary_team_in_list_gets_error(self):
        rollout = RolloutConfig(phase="canary", teams=["payments", "platform"])
        result = apply_rollout(self._fail(), rollout, team="payments")
        assert not result.valid
        assert result.errors

    # canary + team NOT in list → downgrade
    def test_canary_team_not_in_list_gets_warning(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._fail(), rollout, team="fulfillment")
        assert result.valid
        assert not result.errors
        assert result.warnings

    def test_canary_downgrade_includes_original_error_as_warning(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._fail(), rollout, team="other")
        assert any("rule broken" in w for w in result.warnings)

    def test_canary_downgrade_includes_canary_note(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._fail(), rollout, team="other")
        assert any("canary rollout" in w for w in result.warnings)

    def test_canary_downgrade_preserves_existing_warnings(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        base = ValidationResult(valid=False, errors=["oops"], warnings=["pre-existing"])
        result = apply_rollout(base, rollout, team="other")
        assert any("pre-existing" in w for w in result.warnings)

    # canary + no team → treat as not-in-list (advisory warning)
    def test_canary_no_team_gets_warning(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._fail(), rollout, team=None)
        assert result.valid
        assert result.warnings

    def test_canary_no_team_warning_mentions_your_team(self):
        rollout = RolloutConfig(phase="canary", teams=["payments"])
        result = apply_rollout(self._fail(), rollout, team=None)
        assert any("your team" in w for w in result.warnings)


# ── Topic validator with rollout ───────────────────────────────────────────────

def _topic_canary_config(canary_teams: list[str]) -> TopicConfig:
    return TopicConfig(
        segment_count=7,
        prefixes=["raw"],
        rollout=RolloutConfig(phase="canary", teams=canary_teams),
    )


class TestTopicValidatorRollout:

    _BAD_TOPIC = "raw.payments.v1"  # only 3 segments, needs 7

    def test_canary_team_gets_error(self):
        config = _topic_canary_config(["payments"])
        result = validate_topic_name(self._BAD_TOPIC, config, team="payments")
        assert not result.valid
        assert result.errors

    def test_non_canary_team_gets_warning(self):
        config = _topic_canary_config(["payments"])
        result = validate_topic_name(self._BAD_TOPIC, config, team="fulfillment")
        assert result.valid
        assert result.warnings

    def test_stable_rule_applies_to_all_teams(self):
        config = TopicConfig(segment_count=7, prefixes=["raw"])  # no rollout → stable
        result = validate_topic_name(self._BAD_TOPIC, config, team="any-team")
        assert not result.valid

    def test_no_team_on_canary_gets_warning(self):
        config = _topic_canary_config(["payments"])
        result = validate_topic_name(self._BAD_TOPIC, config, team=None)
        assert result.valid
        assert result.warnings

    def test_valid_topic_unaffected_by_rollout(self):
        config = _topic_canary_config(["payments"])
        good = "raw.retail.pos.acme.orders.receipt.v1"
        result = validate_topic_name(good, config, team="fulfillment")
        assert result.valid
        assert not result.errors


# ── RBAC validator with rollout ────────────────────────────────────────────────

def _rbac_canary_config(canary_teams: list[str]) -> RBACConfig:
    return RBACConfig(
        valid_roles=["DeveloperRead"],
        valid_resource_types=["topic"],
        rollout=RolloutConfig(phase="canary", teams=canary_teams),
    )


class TestRBACValidatorRollout:

    def test_canary_team_gets_error(self):
        config = _rbac_canary_config(["payments"])
        result = validate_rbac_binding("BadRole", "topic", "my-topic", config, team="payments")
        assert not result.valid

    def test_non_canary_team_gets_warning(self):
        config = _rbac_canary_config(["payments"])
        result = validate_rbac_binding("BadRole", "topic", "my-topic", config, team="fulfillment")
        assert result.valid
        assert result.warnings

    def test_stable_applies_to_all(self):
        config = RBACConfig(valid_roles=["DeveloperRead"], valid_resource_types=["topic"])
        result = validate_rbac_binding("BadRole", "topic", "my-topic", config, team="any")
        assert not result.valid


# ── SA validator with rollout ──────────────────────────────────────────────────

def _sa_canary_config(canary_teams: list[str]) -> SAConfig:
    return SAConfig(
        prefix="sa-",
        valid_envs=["dev", "prod"],
        rollout=RolloutConfig(phase="canary", teams=canary_teams),
    )


class TestSAValidatorRollout:

    _BAD_SA = "wrong-name"

    def test_canary_team_gets_error(self):
        config = _sa_canary_config(["platform"])
        result = validate_sa_name(self._BAD_SA, config, team="platform")
        assert not result.valid

    def test_non_canary_team_gets_warning(self):
        config = _sa_canary_config(["platform"])
        result = validate_sa_name(self._BAD_SA, config, team="payments")
        assert result.valid
        assert result.warnings

    def test_stable_applies_to_all(self):
        config = SAConfig(prefix="sa-", valid_envs=["dev", "prod"])
        result = validate_sa_name(self._BAD_SA, config, team="payments")
        assert not result.valid


# ── Schema validator with rollout ──────────────────────────────────────────────

def _schema_canary_config(canary_teams: list[str]) -> SchemaConfig:
    return SchemaConfig(
        valid_formats=["AVRO"],
        valid_compatibility_levels=["BACKWARD"],
        rollout=RolloutConfig(phase="canary", teams=canary_teams),
    )


class TestSchemaValidatorRollout:

    def test_canary_team_gets_error(self):
        config = _schema_canary_config(["payments"])
        result = validate_schema_entry("XML", "BACKWARD", config, team="payments")
        assert not result.valid

    def test_non_canary_team_gets_warning(self):
        config = _schema_canary_config(["payments"])
        result = validate_schema_entry("XML", "BACKWARD", config, team="other")
        assert result.valid
        assert result.warnings

    def test_stable_applies_to_all(self):
        config = SchemaConfig(valid_formats=["AVRO"], valid_compatibility_levels=["BACKWARD"])
        result = validate_schema_entry("XML", "BACKWARD", config, team="any")
        assert not result.valid


# ── get_rollout_status tool ────────────────────────────────────────────────────

def _config_with_canary(rule: str) -> GovernanceConfig:
    rollout = RolloutConfig(phase="canary", teams=["payments", "platform"])
    cfg = GovernanceConfig()
    match rule:
        case "kafka.topic":
            cfg.kafka.topic.rollout = rollout
        case "kafka.rbac":
            cfg.kafka.rbac.rollout = rollout
        case "kafka.service_account":
            cfg.kafka.service_account.rollout = rollout
        case "kafka.schema_registry":
            cfg.kafka.schema_registry.rollout = rollout
        case "rest_api":
            cfg.rest_api.rollout = rollout
        case "service":
            cfg.service.rollout = rollout
    return cfg


class TestGetRolloutStatus:

    @pytest.mark.parametrize("rule", [
        "kafka.topic", "kafka.rbac", "kafka.service_account",
        "kafka.schema_registry", "rest_api", "service",
    ])
    def test_canary_status_returned(self, rule):
        cfg = _config_with_canary(rule)
        status = get_rollout_status(rule, cfg)
        assert status.rule_name == rule
        assert status.phase == "canary"
        assert "payments" in status.teams
        assert not status.enforced_for_all

    def test_stable_when_no_rollout(self):
        cfg = GovernanceConfig()
        status = get_rollout_status("kafka.topic", cfg)
        assert status.phase == "stable"
        assert status.enforced_for_all
        assert status.teams == []

    def test_stable_when_phase_is_stable(self):
        cfg = GovernanceConfig()
        cfg.kafka.topic.rollout = RolloutConfig(phase="stable", teams=["payments"])
        status = get_rollout_status("kafka.topic", cfg)
        assert status.phase == "stable"
        assert status.enforced_for_all

    def test_invalid_rule_name_raises(self):
        with pytest.raises(ValueError, match="unknown rule_name"):
            get_rollout_status("nonexistent.rule", GovernanceConfig())

    def test_canary_teams_list_matches(self):
        cfg = _config_with_canary("rest_api")
        status = get_rollout_status("rest_api", cfg)
        assert set(status.teams) == {"payments", "platform"}
