#!/usr/bin/env bash
# govern-mcp bootstrap — run once after cloning the template
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/mcp-server"

echo "==> Setting up govern-mcp..."

# Python venv
cd "$SERVER_DIR"
python3 -m venv .venv
.venv/bin/pip install -q -e ".[dev]"

# .env from example if not present
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "    Created mcp-server/.env — edit GOVERNANCE_REPO_PATH if needed"
fi

echo ""
echo "==> Done. Quick-start:"
echo ""
echo "    # Start the server"
echo "    cd mcp-server && .venv/bin/python -m src.main"
echo ""
echo "    # Run tests"
echo "    cd mcp-server && .venv/bin/pytest tests/ -q && .venv/bin/behave"
echo ""
echo "    # Validate a topic name from the CLI"
echo "    cd mcp-server && .venv/bin/governance-validate topic raw.sales.pos.hmsu.commons.guestcheck.v1"
echo ""
echo "    # Connect Claude Code — add to any project's .mcp.json:"
echo '    {"mcpServers":{"govern-mcp":{"type":"http","url":"http://127.0.0.1:8080/mcp"}}}'
