"""Tests for NOMOS_ON_UNAVAILABLE — server fail-closed / fail-open behaviour.

The env var controls what happens when the governance repo cannot be loaded:
  "fail"  (default) → RuntimeError is raised; request halts.
  "warn"            → warning is logged; server continues with an empty config.
"""
import logging
from pathlib import Path

import pytest

import src.server as server_module
from src.config import settings
from src.loaders.local_loader import LocalLoader

# A governance repo path that is guaranteed not to exist.
_NONEXISTENT_REPO = Path("/nonexistent-governance-repo-that-does-not-exist")


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_cached_config(monkeypatch):
    """Clear the module-level config cache before and after every test."""
    monkeypatch.setattr(server_module, "_governance_config", None)
    yield
    monkeypatch.setattr(server_module, "_governance_config", None)


@pytest.fixture()
def bad_loader(monkeypatch):
    """Patch server._loader() to return a LocalLoader pointing at a non-existent path."""
    loader = LocalLoader(_NONEXISTENT_REPO)
    monkeypatch.setattr(server_module, "_loader", lambda: loader)


# ---------------------------------------------------------------------------
# Default setting
# ---------------------------------------------------------------------------

def test_on_unavailable_default_is_fail():
    """NOMOS_ON_UNAVAILABLE defaults to 'fail' — fail-closed out of the box."""
    assert settings.on_unavailable == "fail"


# ---------------------------------------------------------------------------
# fail mode
# ---------------------------------------------------------------------------

def test_fail_mode_raises_runtime_error(monkeypatch, bad_loader):
    """When NOMOS_ON_UNAVAILABLE=fail and the repo is missing, _config() raises RuntimeError."""
    monkeypatch.setattr(settings, "on_unavailable", "fail")

    with pytest.raises(RuntimeError, match="Governance repo unavailable"):
        server_module._config()


def test_fail_mode_error_mentions_warn_hint(monkeypatch, bad_loader):
    """The RuntimeError message hints at setting NOMOS_ON_UNAVAILABLE=warn."""
    monkeypatch.setattr(settings, "on_unavailable", "fail")

    with pytest.raises(RuntimeError, match="warn"):
        server_module._config()


def test_fail_mode_retries_on_each_call(monkeypatch, bad_loader):
    """In fail mode the config is NOT cached after a failure — every call retries."""
    monkeypatch.setattr(settings, "on_unavailable", "fail")

    with pytest.raises(RuntimeError):
        server_module._config()

    # Second call should also raise (not silently succeed with None).
    with pytest.raises(RuntimeError):
        server_module._config()


# ---------------------------------------------------------------------------
# warn mode
# ---------------------------------------------------------------------------

def test_warn_mode_returns_empty_config(monkeypatch, bad_loader):
    """When NOMOS_ON_UNAVAILABLE=warn and the repo is missing, an empty config is returned."""
    monkeypatch.setattr(settings, "on_unavailable", "warn")

    config = server_module._config()

    assert config is not None


def test_warn_mode_logs_warning(monkeypatch, bad_loader, caplog):
    """Warn mode emits a WARNING-level log message."""
    monkeypatch.setattr(settings, "on_unavailable", "warn")

    with caplog.at_level(logging.WARNING, logger="src.server"):
        server_module._config()

    warning_texts = [r.message.lower() for r in caplog.records if r.levelno == logging.WARNING]
    assert any("governance repo unavailable" in t for t in warning_texts), (
        f"Expected a warning containing 'governance repo unavailable'; got: {warning_texts}"
    )


def test_warn_mode_caches_empty_config(monkeypatch, bad_loader):
    """After the first warn, _config() returns the same (empty) config object without retrying."""
    monkeypatch.setattr(settings, "on_unavailable", "warn")

    config1 = server_module._config()
    config2 = server_module._config()

    assert config1 is config2


# ---------------------------------------------------------------------------
# LocalLoader.validate() unit tests
# ---------------------------------------------------------------------------

def test_local_loader_validate_raises_for_missing_path():
    """LocalLoader.validate() raises FileNotFoundError when the repo path does not exist."""
    loader = LocalLoader(_NONEXISTENT_REPO)

    with pytest.raises(FileNotFoundError, match="Governance repo not found"):
        loader.validate()


def test_local_loader_validate_passes_for_existing_path(tmp_path):
    """LocalLoader.validate() is silent when the repo path exists."""
    loader = LocalLoader(tmp_path)
    loader.validate()  # must not raise
