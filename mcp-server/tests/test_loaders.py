from pathlib import Path
from src.loaders.local_loader import LocalLoader

REPO_ROOT = Path(__file__).parent.parent.parent / "examples" / "kafka"


def test_local_loader_read_constitution():
    loader = LocalLoader(REPO_ROOT)
    content = loader.read("constitution.md")
    assert len(content) > 0


def test_local_loader_read_missing_raises():
    loader = LocalLoader(REPO_ROOT)
    try:
        loader.read("does-not-exist.md")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_local_loader_list_adrs():
    loader = LocalLoader(REPO_ROOT)
    paths = loader.list("adrs/global")
    assert any("001-" in p for p in paths)


def test_local_loader_list_checks():
    loader = LocalLoader(REPO_ROOT)
    paths = loader.list("features/kafka")
    assert any("topic-naming.feature" in p for p in paths)
