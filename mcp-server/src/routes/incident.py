"""
Incident-to-Eval Synthesis — POST /webhook/incident

Accepts a governance violation report, formats it as a failures.md entry, and
opens a pull request against the governance repository so the violation becomes
visible to agents via get_knowledge("failures") after the PR is merged.

Environment variables required:
  GITHUB_TOKEN     — personal access token with `repo` scope (fail-closed if absent)
  NOMOS_REPO_PATH  — {owner}/{repo} of the governance repo, e.g. "my-org/governance"

Returns:
  { queued: true, pr_url: "...", entry_preview: "..." }
"""
import base64
import logging
import re
from datetime import date, timezone, datetime

import httpx
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.config import settings

logger = logging.getLogger(__name__)

_KNOWLEDGE_PATH = "knowledge/failures.md"
_FAILURES_HEADER = (
    "# Failure Patterns\n\n"
    "Systematic AI mistakes observed in production, automatically synthesised "
    "from governance violations caught in CI.\n\n"
    "Query via `get_knowledge(\"failures\")` before generating resources.\n\n"
    "---\n"
)


# ── Payload ────────────────────────────────────────────────────────────────────

class IncidentPayload(BaseModel):
    resource_name: str    # the specific resource that violated the rule
    resource_type: str    # kafka_topic | rbac | sa | schema | rest_path | service_name
    rule_violated: str    # human-readable description of the rule that was broken
    bad_pattern: str      # the exact bad value / shape that was observed
    correct_pattern: str  # what the value / shape should have been


# ── Entry formatting ───────────────────────────────────────────────────────────

def format_entry(payload: IncidentPayload, *, reported_date: str | None = None) -> str:
    """Format a violation as a failures.md entry.

    Pure function — no I/O.  ``reported_date`` is injectable for tests;
    defaults to today (ISO 8601).
    """
    today = reported_date or date.today().isoformat()
    return (
        f"\n## {payload.rule_violated} — `{payload.resource_type}`\n\n"
        f"- **Resource:** `{payload.resource_name}` (`{payload.resource_type}`)\n"
        f"- **Bad pattern:** `{payload.bad_pattern}`\n"
        f"- **Correct pattern:** `{payload.correct_pattern}`\n"
        f"- **Rule violated:** {payload.rule_violated}\n"
        f"- **Reported:** {today}\n\n"
        "---\n"
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _branch_slug(text: str) -> str:
    """Convert arbitrary text into a URL-safe, 40-char-max branch name segment."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40]


def _repo_path() -> str:
    """
    Return the {owner}/{repo} of the governance repo.

    Prefers NOMOS_REPO_PATH; falls back to extracting from GOVERNANCE_REPO_URL
    when the server is running in GitHub mode.
    """
    if settings.nomos_repo_path:
        return settings.nomos_repo_path
    if settings.governance_repo_url:
        parts = settings.governance_repo_url.rstrip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return ""


# ── GitHub API ─────────────────────────────────────────────────────────────────

async def _create_pr(payload: IncidentPayload, entry: str) -> str:
    """Append entry to knowledge/failures.md and open a PR.

    Returns the HTML URL of the new PR.
    Raises RuntimeError for configuration problems, httpx errors for API problems.
    """
    token = settings.github_token
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set — cannot open incident PR. "
            "Set GITHUB_TOKEN (repo scope) to enable Incident-to-Eval Synthesis."
        )

    repo = _repo_path()
    if not repo:
        raise RuntimeError(
            "Cannot determine governance repo. "
            "Set NOMOS_REPO_PATH to {owner}/{repo} "
            "(e.g. my-org/governance) or set GOVERNANCE_REPO_URL in GitHub mode."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    api = "https://api.github.com"
    today = date.today().isoformat()
    branch = f"incident/{today}-{_branch_slug(payload.rule_violated)}"

    async with httpx.AsyncClient(headers=headers, timeout=15) as client:

        # 1 — main branch SHA
        r = await client.get(f"{api}/repos/{repo}/git/ref/heads/main")
        r.raise_for_status()
        main_sha = r.json()["object"]["sha"]

        # 2 — existing failures.md (may not exist yet)
        existing_content = ""
        existing_sha: str | None = None
        r = await client.get(f"{api}/repos/{repo}/contents/{_KNOWLEDGE_PATH}")
        if r.status_code == 200:
            data = r.json()
            existing_content = base64.b64decode(data["content"]).decode("utf-8")
            existing_sha = data["sha"]
        elif r.status_code != 404:
            r.raise_for_status()

        # 3 — create incident branch
        r = await client.post(
            f"{api}/repos/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": main_sha},
        )
        r.raise_for_status()

        # 4 — write updated failures.md on the new branch
        new_content = (existing_content + entry) if existing_content else (_FAILURES_HEADER + entry)
        file_body: dict = {
            "message": (
                f"knowledge: add failure pattern for {payload.resource_type} violation\n\n"
                f"Resource: {payload.resource_name}\n"
                f"Rule: {payload.rule_violated}"
            ),
            "content": base64.b64encode(new_content.encode()).decode(),
            "branch": branch,
        }
        if existing_sha:
            file_body["sha"] = existing_sha
        r = await client.put(
            f"{api}/repos/{repo}/contents/{_KNOWLEDGE_PATH}",
            json=file_body,
        )
        r.raise_for_status()

        # 5 — open PR
        rule_title = payload.rule_violated[:60]
        r = await client.post(
            f"{api}/repos/{repo}/pulls",
            json={
                "title": f"knowledge: {payload.resource_type} failure — {rule_title}",
                "body": (
                    "## Incident-to-Eval Synthesis\n\n"
                    "Governance violation caught in production, automatically synthesised "
                    "into a `failures.md` entry.\n\n"
                    f"**Resource:** `{payload.resource_name}` (`{payload.resource_type}`)\n"
                    f"**Rule violated:** {payload.rule_violated}\n"
                    f"**Bad pattern:** `{payload.bad_pattern}`\n"
                    f"**Correct pattern:** `{payload.correct_pattern}`\n\n"
                    "Review and merge to make this pattern visible to agents via "
                    "`get_knowledge(\"failures\")`."
                ),
                "head": branch,
                "base": "main",
            },
        )
        r.raise_for_status()
        return r.json()["html_url"]


# ── Handler ────────────────────────────────────────────────────────────────────

async def incident_webhook(request: Request) -> JSONResponse:
    """POST /webhook/incident — report a governance violation and open a PR."""

    # Fail closed: no token → hard stop, not a silent no-op.
    if not settings.github_token:
        logger.error(
            "incident webhook: GITHUB_TOKEN not set — rejecting request (fail-closed)"
        )
        return JSONResponse(
            {
                "error": (
                    "GITHUB_TOKEN is not set. "
                    "Incident-to-Eval Synthesis is unavailable until a token with "
                    "repo scope is configured."
                )
            },
            status_code=503,
        )

    try:
        body = await request.json()
        payload = IncidentPayload(**body)
    except Exception as exc:
        return JSONResponse({"error": f"invalid payload: {exc}"}, status_code=400)

    logger.info(
        "incident webhook: resource=%s type=%s rule=%r",
        payload.resource_name,
        payload.resource_type,
        payload.rule_violated,
    )

    entry = format_entry(payload)

    try:
        pr_url = await _create_pr(payload, entry)
    except RuntimeError as exc:
        logger.error("incident webhook config error: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=503)
    except httpx.HTTPStatusError as exc:
        logger.error("incident webhook GitHub API error: %s %s", exc.response.status_code, exc)
        return JSONResponse(
            {"error": f"GitHub API returned {exc.response.status_code}"},
            status_code=502,
        )
    except httpx.RequestError as exc:
        logger.error("incident webhook network error: %s", exc)
        return JSONResponse({"error": f"network error reaching GitHub: {exc}"}, status_code=502)

    logger.info("incident webhook: PR opened at %s", pr_url)
    return JSONResponse({"queued": True, "pr_url": pr_url, "entry_preview": entry})


routes = [
    Route("/webhook/incident", incident_webhook, methods=["POST"]),
]
