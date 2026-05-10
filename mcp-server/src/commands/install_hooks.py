"""
nomos install-hooks — install .mcp.json and pre-commit hook in a project repository.

Usage:
    nomos install-hooks --server https://governance.acme.com
    nomos install-hooks --server https://governance.acme.com --project-dir /path/to/repo
    nomos install-hooks --force   # overwrite existing files
"""
import json
import stat
from pathlib import Path

_MCP_JSON = {
    "mcpServers": {
        "nomos": {
            "type": "http",
            "url": "{server_url}/mcp",
        }
    }
}

_PRE_COMMIT_HOOK = """\
#!/usr/bin/env bash
# nomos pre-commit hook
# Validates staged resources against the governance server before each commit.
# Customize the sections below for your project structure.
#
# Installed by: nomos install-hooks
# Docs: https://github.com/your-org/nomos-template/blob/main/DEPLOYMENT.md

set -euo pipefail

NOMOS_SERVER="{server_url}"

# ── Topic validation ─────────────────────────────────────────────────────────
# Uncomment and adapt to extract topic names from your staged HCL files.
#
# STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep "topics\\.hcl" || true)
# for f in $STAGED; do
#   # Extract topic keys and validate each one
#   # Example: grep -oP '(?<=")(\\S+\\.v\\d+)(?=")' "$f" | while read -r name; do
#   #   nomos-validate --server "$NOMOS_SERVER" topic "$name"
#   # done
#   echo "nomos: skipping topic validation for $f (configure above)"
# done

# ── SA validation ────────────────────────────────────────────────────────────
# Uncomment and adapt to validate service account names in staged files.
#
# STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep "rbac\\.hcl" || true)
# for f in $STAGED; do
#   nomos-validate --server "$NOMOS_SERVER" sa <extracted-sa-name>
# done

exit 0
"""


def run(args) -> int:
    project_dir = Path(args.project_dir).resolve()
    server_url = args.server.rstrip("/") if args.server else "https://governance.your-org.com"

    # .mcp.json
    mcp_path = project_dir / ".mcp.json"
    if mcp_path.exists() and not args.force:
        print(f"SKIP {mcp_path} already exists (use --force to overwrite)")
    else:
        config = json.loads(
            json.dumps(_MCP_JSON).replace("{server_url}", server_url)
        )
        mcp_path.write_text(json.dumps(config, indent=2) + "\n")
        status = "updated" if mcp_path.exists() else "created"
        print(f"OK   {mcp_path}")

    # pre-commit hook
    git_dir = project_dir / ".git"
    if not git_dir.is_dir():
        print(f"WARN .git not found at {project_dir} — skipping hook installation")
        print(f"     Run from inside a git repository to install the pre-commit hook")
        return 0

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists() and not args.force:
        print(f"SKIP {hook_path} already exists (use --force to overwrite)")
    else:
        hook_path.write_text(_PRE_COMMIT_HOOK.replace("{server_url}", server_url))
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"OK   {hook_path}")

    print()
    if args.server:
        print(f"Agent queries:  {server_url}/mcp")
        print(f"CLI validation: nomos-validate --server {server_url} topic <name>")
    else:
        print("Edit .mcp.json and .git/hooks/pre-commit to set your governance server URL.")

    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "install-hooks",
        help="Install .mcp.json and pre-commit hook in a project repository",
    )
    p.add_argument(
        "--server",
        metavar="URL",
        help="Nomos server URL (e.g. https://governance.acme.com)",
    )
    p.add_argument(
        "--project-dir",
        metavar="PATH",
        default=".",
        help="Project repository to install into (default: current directory)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .mcp.json and pre-commit hook",
    )
    p.set_defaults(func=run)
