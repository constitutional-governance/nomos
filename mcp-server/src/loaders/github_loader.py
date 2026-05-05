import base64
import time
import httpx
from .base_loader import BaseLoader


class GitHubLoader(BaseLoader):
    def __init__(self, repo_url: str, token: str, branch: str, ttl: int) -> None:
        # repo_url: https://github.com/org/repo
        parts = repo_url.rstrip("/").split("/")
        self._owner = parts[-2]
        self._repo = parts[-1]
        self._branch = branch
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        self._ttl = ttl
        self._cache: dict[str, tuple[str, float]] = {}

    def _api(self, path: str) -> str:
        now = time.monotonic()
        if path in self._cache:
            content, ts = self._cache[path]
            if now - ts < self._ttl:
                return content

        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/contents/{path}?ref={self._branch}"
        r = httpx.get(url, headers=self._headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        self._cache[path] = (content, now)
        return content

    def read(self, relative_path: str) -> str:
        try:
            return self._api(relative_path)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(relative_path)
            raise

    def list(self, relative_dir: str) -> list[str]:
        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/trees/{self._branch}?recursive=1"
        r = httpx.get(url, headers=self._headers, timeout=10)
        r.raise_for_status()
        tree = r.json().get("tree", [])
        prefix = relative_dir.rstrip("/") + "/"
        return sorted(
            item["path"] for item in tree
            if item["type"] == "blob" and item["path"].startswith(prefix)
        )

    def invalidate(self) -> None:
        self._cache.clear()
