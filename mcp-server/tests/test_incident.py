"""Tests for POST /webhook/incident — Incident-to-Eval Synthesis.

All tests here are purely local: no GitHub API calls are made.
The key function under test is format_entry(), which is a pure function,
plus _branch_slug(), _repo_path(), and the handler's fail-closed behaviour.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.routes.incident import (
    IncidentPayload,
    format_entry,
    _branch_slug,
    _repo_path,
    _FAILURES_HEADER,
)
from src.config import settings


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _payload(**overrides) -> IncidentPayload:
    defaults = dict(
        resource_name="raw.payments.checkout.v1",
        resource_type="kafka_topic",
        rule_violated="Topic must have exactly 7 dot-separated segments",
        bad_pattern="raw.payments.checkout.v1",
        correct_pattern="raw.payments.pos.acme.checkout.receipt.v1",
    )
    defaults.update(overrides)
    return IncidentPayload(**defaults)


# ── format_entry: field presence ───────────────────────────────────────────────

def test_entry_contains_resource_name():
    assert "raw.payments.checkout.v1" in format_entry(_payload())


def test_entry_contains_resource_type():
    assert "kafka_topic" in format_entry(_payload())


def test_entry_contains_rule_violated():
    assert "Topic must have exactly 7 dot-separated segments" in format_entry(_payload())


def test_entry_contains_bad_pattern():
    assert "raw.payments.checkout.v1" in format_entry(_payload())


def test_entry_contains_correct_pattern():
    assert "raw.payments.pos.acme.checkout.receipt.v1" in format_entry(_payload())


def test_entry_contains_injected_date():
    entry = format_entry(_payload(), reported_date="2026-05-27")
    assert "2026-05-27" in entry


def test_entry_defaults_to_today():
    from datetime import date
    entry = format_entry(_payload())
    assert date.today().isoformat() in entry


# ── format_entry: structure ────────────────────────────────────────────────────

def test_entry_ends_with_separator():
    """Entry must end with --- so appending multiple entries stays parseable."""
    assert format_entry(_payload()).strip().endswith("---")


def test_entry_has_markdown_h2_heading():
    """First non-blank line is a ## heading containing resource_type."""
    lines = [l for l in format_entry(_payload()).splitlines() if l.strip()]
    heading = lines[0]
    assert heading.startswith("##")
    assert "kafka_topic" in heading


def test_entry_heading_contains_rule():
    lines = [l for l in format_entry(_payload()).splitlines() if l.strip()]
    heading = lines[0]
    assert "Topic must have exactly 7 dot-separated segments" in heading


def test_entry_bullet_bad_pattern():
    lines = format_entry(_payload()).splitlines()
    bad_line = next((l for l in lines if "Bad pattern" in l), None)
    assert bad_line is not None, "No 'Bad pattern' bullet found"
    assert "raw.payments.checkout.v1" in bad_line


def test_entry_bullet_correct_pattern():
    lines = format_entry(_payload()).splitlines()
    correct_line = next((l for l in lines if "Correct pattern" in l), None)
    assert correct_line is not None, "No 'Correct pattern' bullet found"
    assert "raw.payments.pos.acme.checkout.receipt.v1" in correct_line


def test_entry_bullet_resource():
    lines = format_entry(_payload()).splitlines()
    resource_line = next((l for l in lines if "Resource:" in l), None)
    assert resource_line is not None, "No 'Resource' bullet found"
    assert "raw.payments.checkout.v1" in resource_line


# ── format_entry: multiple resource types ─────────────────────────────────────

@pytest.mark.parametrize("resource_type,resource_name,rule", [
    ("rbac", "DeveloperRead on group/my-group", "Role applied to wrong resource type"),
    ("sa", "sa-acme-connector-source-jdbc", "SA name must include environment suffix"),
    ("schema", "AVRO/FULL_TRANSITIVE", "Compatibility level not in allowed list"),
    ("rest_path", "/orders", "REST path must start with version prefix"),
    ("service_name", "My_Service", "Service name must be lowercase kebab-case"),
])
def test_entry_works_for_all_resource_types(resource_type, resource_name, rule):
    p = _payload(resource_type=resource_type, resource_name=resource_name, rule_violated=rule)
    entry = format_entry(p)
    assert resource_type in entry
    assert resource_name in entry
    assert rule in entry
    assert entry.strip().endswith("---")


# ── _branch_slug ───────────────────────────────────────────────────────────────

def test_branch_slug_removes_spaces():
    assert " " not in _branch_slug("Topic must have exactly 7 segments")


def test_branch_slug_is_lowercase():
    assert _branch_slug("UPPER CASE TEXT") == _branch_slug("UPPER CASE TEXT").lower()


def test_branch_slug_truncates_at_40():
    slug = _branch_slug("a" * 100)
    assert len(slug) <= 40


def test_branch_slug_replaces_special_chars():
    slug = _branch_slug("topic.name/violation: bad!")
    assert all(c.isalnum() or c == "-" for c in slug)


def test_branch_slug_stable_for_same_input():
    rule = "Topic must have exactly 7 dot-separated segments"
    assert _branch_slug(rule) == _branch_slug(rule)


# ── _repo_path ─────────────────────────────────────────────────────────────────

def test_repo_path_uses_nomos_repo_path(monkeypatch):
    monkeypatch.setattr(settings, "nomos_repo_path", "my-org/governance")
    assert _repo_path() == "my-org/governance"


def test_repo_path_falls_back_to_governance_repo_url(monkeypatch):
    monkeypatch.setattr(settings, "nomos_repo_path", "")
    monkeypatch.setattr(settings, "governance_repo_url", "https://github.com/my-org/governance-repo")
    assert _repo_path() == "my-org/governance-repo"


def test_repo_path_empty_when_neither_set(monkeypatch):
    monkeypatch.setattr(settings, "nomos_repo_path", "")
    monkeypatch.setattr(settings, "governance_repo_url", "")
    assert _repo_path() == ""


# ── handler: fail-closed ───────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_handler_returns_503_when_no_token(monkeypatch):
    """Handler must return 503 immediately when GITHUB_TOKEN is not set."""
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from src.routes.incident import routes

    monkeypatch.setattr(settings, "github_token", "")
    app = Starlette(routes=routes)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/webhook/incident",
        json={
            "resource_name": "raw.payments.checkout.v1",
            "resource_type": "kafka_topic",
            "rule_violated": "Topic must have 7 segments",
            "bad_pattern": "raw.payments.checkout.v1",
            "correct_pattern": "raw.payments.pos.acme.checkout.receipt.v1",
        },
    )

    assert response.status_code == 503
    body = response.json()
    assert "GITHUB_TOKEN" in body["error"]


@pytest.mark.anyio
async def test_handler_returns_400_for_missing_fields(monkeypatch):
    """Handler must return 400 for a malformed payload."""
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from src.routes.incident import routes

    monkeypatch.setattr(settings, "github_token", "ghp_fake_token")
    app = Starlette(routes=routes)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/webhook/incident",
        json={"resource_name": "only-one-field"},
    )

    assert response.status_code == 400
    assert "error" in response.json()
