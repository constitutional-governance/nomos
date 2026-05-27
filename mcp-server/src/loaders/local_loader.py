from pathlib import Path
from .base_loader import BaseLoader


class LocalLoader(BaseLoader):
    def __init__(self, repo_path: Path) -> None:
        self._root = repo_path.resolve()

    def validate(self) -> None:
        """Raise FileNotFoundError if the governance repo directory does not exist."""
        if not self._root.exists():
            raise FileNotFoundError(
                f"Governance repo not found at {self._root!s}. "
                "Check GOVERNANCE_REPO_PATH or the --repo argument."
            )

    def read(self, relative_path: str) -> str:
        full = self._root / relative_path
        if not full.exists():
            raise FileNotFoundError(f"{relative_path} not found in {self._root}")
        return full.read_text(encoding="utf-8")

    def list(self, relative_dir: str) -> list[str]:
        base = self._root / relative_dir
        if not base.exists():
            return []
        return [
            str(p.relative_to(self._root))
            for p in sorted(base.rglob("*"))
            if p.is_file()
        ]
