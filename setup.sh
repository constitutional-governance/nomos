#!/usr/bin/env bash
# Nomos bootstrap — run once after cloning
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/mcp-server"

echo "==> Setting up Nomos..."

cd "$SERVER_DIR"
python3 -m venv .venv
.venv/bin/pip install -q -e ".[dev]"

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "    Created mcp-server/.env — set GOVERNANCE_REPO_PATH to your governance repo"
fi

echo ""
echo "==> Done. Quick-start:"
echo ""
echo "    # Start the server"
echo "    cd mcp-server && .venv/bin/nomos"
echo ""
echo "    # Run tests"
echo "    cd mcp-server && .venv/bin/pytest tests/ -q && .venv/bin/behave"
echo ""
echo "    # Validate a resource name from the CLI"
echo "    cd mcp-server && .venv/bin/nomos-validate topic acme.payments.checkout.team.receipts.transaction.v1"
echo ""
echo "    # Connect Claude Code — add to your project's .mcp.json:"
echo '    {"mcpServers":{"nomos":{"type":"http","url":"http://127.0.0.1:8080/mcp"}}}'
