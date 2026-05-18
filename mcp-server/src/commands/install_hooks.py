"""
nomos install-hooks — install AI agent config and pre-commit hook in a project repository.

Usage:
    nomos install-hooks --server https://governance.acme.com
    nomos install-hooks --server https://governance.acme.com --tool all
    nomos install-hooks --server https://governance.acme.com --tool copilot
    nomos install-hooks --force   # overwrite existing files

--tool options:
    all      Install config for all supported tools (default)
    mcp      .mcp.json only — for MCP-compatible agents (Claude Code, Cursor, Windsurf, ...)
    copilot  .github/copilot-instructions.md only — for GitHub Copilot
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
# nomos pre-commit hook — validates staged HCL resources before each commit.
# Installed by: nomos install-hooks

set -euo pipefail

NOMOS_SERVER="{server_url}"
ERRORS=0

# Resolve nomos-validate: remote mode if server is set, local mode otherwise.
if [ -n "$NOMOS_SERVER" ] && [ "$NOMOS_SERVER" != "https://governance.your-org.com" ]; then
  NOMOS_CMD="nomos-validate --server $NOMOS_SERVER"
else
  NOMOS_CMD="nomos-validate"
fi

# Guard: skip silently if nomos-validate is not installed.
if ! command -v nomos-validate &>/dev/null; then
  echo "nomos: nomos-validate not found — skipping governance checks (run: pip install nomos-mcp)"
  exit 0
fi

# ── Topic validation ──────────────────────────────────────────────────────────
STAGED_TOPICS=$(git diff --cached --name-only --diff-filter=ACM | grep "topics\\.hcl$" || true)
for f in $STAGED_TOPICS; do
  # Extract quoted topic-name keys: lines that match <prefix>.<segments>.v<n> as map keys
  NAMES=$(grep -oP '"(raw|public|ready|private|kstreams|kcamel|sink|landing|dev)\\.[^"]{6,}\\.v[0-9]+"' "$f" \
          | tr -d '"' || true)
  for name in $NAMES; do
    if ! $NOMOS_CMD topic "$name" 2>&1; then
      ERRORS=$((ERRORS + 1))
    fi
  done
done

# ── SA validation ─────────────────────────────────────────────────────────────
STAGED_RBAC=$(git diff --cached --name-only --diff-filter=ACM | grep "rbac\\.hcl$" || true)
for f in $STAGED_RBAC; do
  SA_NAMES=$(grep -oP '"sa-[a-z0-9][a-z0-9-]+"' "$f" | tr -d '"' || true)
  for name in $SA_NAMES; do
    if ! $NOMOS_CMD sa "$name" 2>&1; then
      ERRORS=$((ERRORS + 1))
    fi
  done
done

# ── Schema validation ─────────────────────────────────────────────────────────
STAGED_SCHEMAS=$(git diff --cached --name-only --diff-filter=ACM | grep "schemas\\.hcl$" || true)
for f in $STAGED_SCHEMAS; do
  # Extract format values: "format" = "AVRO" / "JSON" / "PROTOBUF"
  # Extract compatibility_level values: "compatibility_level" = "BACKWARD" etc.
  # Validate each unique format+compatibility pair found in the file.
  FORMATS=$(grep -oP '(?<="format"\\s{0,4}=\\s{0,4}")[A-Z]+"' "$f" | tr -d '"' || true)
  COMPAT=$(grep -oP '(?<="compatibility_level"\\s{0,4}=\\s{0,4}")[A-Z_]+"' "$f" | tr -d '"' || true)
  # Validate each format against the default compatibility (full cross-product not needed in pre-commit)
  for fmt in $(echo "$FORMATS" | sort -u); do
    for compat in $(echo "$COMPAT" | sort -u); do
      if ! $NOMOS_CMD schema "$fmt" "$compat" 2>&1; then
        ERRORS=$((ERRORS + 1))
      fi
    done
  done
done

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "nomos: $ERRORS governance violation(s) found — commit blocked."
  echo "       Fix the errors above or run: nomos-validate --help"
  exit 1
fi

exit 0
"""


_COPILOT_INSTRUCTIONS = """\
# Platform Governance

This repository uses the Nomos governance CLI (`nomos-validate`).
Always validate resources before proposing them.

## Before generating or modifying resources

Validate using the CLI. Run these commands in the terminal:

```bash
# Kafka topic name
nomos-validate --server {server_url} topic "raw.retail.pos.acme.orders.receipt.v1"

# RBAC binding
nomos-validate --server {server_url} rbac DeveloperRead topic "raw.retail.*"

# Service account name
nomos-validate --server {server_url} sa "sa-retail-connector-source-jdbc-prod"

# Schema entry
nomos-validate --server {server_url} schema AVRO BACKWARD

# REST API path
nomos-validate --server {server_url} rest-path "/v1/orders/{orderId}/items"

# Microservice name
nomos-validate --server {server_url} service-name "retail-order-api"
```

Exit code `0` means valid. Exit code `1` means invalid — read the output and fix before returning.
Warnings (prefixed `WARNING:`) are advisory.

## Install

```bash
pip install nomos
```

## Key rules

<!-- nomos: auto-generated — run `nomos refresh-instructions --project-dir .` to embed current rules -->
"""


def _write_mcp_json(project_dir: Path, mcp_url: str, force: bool) -> None:
    mcp_path = project_dir / ".mcp.json"
    if mcp_path.exists() and not force:
        print(f"SKIP {mcp_path} already exists (use --force to overwrite)")
        return
    config = json.loads(json.dumps(_MCP_JSON).replace("{server_url}", mcp_url))
    mcp_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"OK   {mcp_path}")


def _write_copilot_instructions(project_dir: Path, server_url: str, force: bool) -> None:
    github_dir = project_dir / ".github"
    github_dir.mkdir(exist_ok=True)
    instructions_path = github_dir / "copilot-instructions.md"
    if instructions_path.exists() and not force:
        print(f"SKIP {instructions_path} already exists (use --force to overwrite)")
        return
    instructions_path.write_text(_COPILOT_INSTRUCTIONS.replace("{server_url}", server_url))
    print(f"OK   {instructions_path}")


def run(args) -> int:
    project_dir = Path(args.project_dir).resolve()
    server_url = args.server.rstrip("/") if args.server else "https://governance.your-org.com"
    tool = getattr(args, "tool", "all")
    if args.team:
        mcp_url = f"{server_url}/teams/{args.team}"
    else:
        mcp_url = server_url

    if tool in ("all", "mcp"):
        _write_mcp_json(project_dir, mcp_url, args.force)

    if tool in ("all", "copilot"):
        _write_copilot_instructions(project_dir, server_url, args.force)

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
        if tool in ("all", "mcp"):
            print(f"MCP endpoint:   {mcp_url}/mcp  (Claude Code, Cursor, Windsurf, ...)")
        if tool in ("all", "copilot"):
            print(f"Copilot rules:  {project_dir}/.github/copilot-instructions.md")
        if args.team:
            print(f"Team context:   {args.team}")
        print(f"REST validate:  {server_url}/validate/topic  (model-agnostic)")
    else:
        print("Edit generated files to set your governance server URL.")

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
        "--team",
        metavar="NAME",
        help="Team name — agent will query team-scoped rules at /teams/<name>/mcp",
    )
    p.add_argument(
        "--tool",
        choices=["all", "mcp", "copilot"],
        default="all",
        help="Which AI tool to configure: all (default), mcp (Claude Code/Cursor/Windsurf), copilot",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    p.set_defaults(func=run)
