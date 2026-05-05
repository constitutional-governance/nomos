# govern-mcp

An AI governance server for engineering teams. Delivers architectural decisions, naming conventions, and executable compliance checks to any MCP-compatible AI agent — Claude Code, GitHub Copilot, Cursor, and others.

Agents connected to govern-mcp can read your ADRs, validate names against your conventions, and receive the right context before touching a Kafka topic, a service account, or a Helm chart.

## What it does

- **Serves knowledge** — ADRs, constitutions, naming conventions available as MCP tools
- **Validates in real time** — topic names, RBAC bindings, and service account names checked against `governance.yml`
- **Runs executable checks** — Gherkin scenarios with Behave; `@enforced` scenarios run in CI
- **Adapts to your org** — edit `governance.yml` to match your conventions; no code changes needed

## Repository layout

```
govern-mcp/
├── governance.yml          # Your org's rules — the only file most adopters edit
├── constitutions/          # Domain constitutions (kafka, camel, springboot, helm)
├── adrs/                   # Architecture Decision Records
│   └── global/             # Platform-wide decisions (ADR-001 … ADR-011)
├── conventions/            # Naming reference, Helm structure, SpecKit guide
├── templates/              # Client config templates (Claude Code, Copilot, VS Code)
├── mcp-server/             # The MCP server (Python, FastMCP)
│   ├── src/
│   │   ├── server.py       # MCP tool definitions
│   │   ├── validators/     # Topic, RBAC, SA naming validators
│   │   ├── loaders/        # Local filesystem and GitHub API loaders
│   │   └── models/         # Pydantic config and response models
│   ├── features/           # Behave Gherkin scenarios (executable checks)
│   └── tests/              # Pytest unit tests
└── setup.sh                # Bootstrap script
```

## Getting started

```bash
git clone https://github.com/your-org/govern-mcp
cd govern-mcp
./setup.sh
```

Then edit `governance.yml` to match your naming conventions and RBAC roles.

Start the server:

```bash
cd mcp-server
.venv/bin/python -m src.main   # http://127.0.0.1:8080
```

Connect a project to it — add `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "govern-mcp": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

## Available MCP tools

| Tool | Purpose |
|---|---|
| `get_constitution(domain)` | Domain principles — call before architectural decisions |
| `get_kafka_conventions()` | Topic naming, RBAC, schema subjects, consumer groups |
| `get_camel_conventions()` | Route IDs, application names, consumer group alignment |
| `get_naming_conventions(type)` | Pattern + examples for one resource type |
| `get_adr(id)` | Full ADR content by ID |
| `search_adrs(query)` | Full-text search across ADRs |
| `list_adrs()` | Discover all governance decisions |
| `get_checks(domain)` | Gherkin checks to validate before a PR |
| `get_springboot_checks()` | Before modifying application-docker.yml |
| `get_helm_template(service_type)` | Ready-to-use Helm values.yml template |
| `validate_topic_name(name)` | Validate against governance.yml rules |
| `validate_rbac_binding(role, type, name)` | Validate an RBAC binding |
| `validate_sa_name(name)` | Validate a service account name |

## Customizing for your organization

`governance.yml` is the single file that makes govern-mcp yours. It controls:

- **Topic rules**: segment count, valid prefixes, max length, non-production prefixes
- **RBAC rules**: valid roles, resource types, admin role constraints
- **Service account rules**: name prefix, valid environments, connector directions

Everything else — ADRs, constitutions, conventions — is Markdown you edit directly.

## Running in production (GitHub mode)

Point the server at your governance repo on GitHub so any team can get live updates:

```bash
# mcp-server/.env
GOVERNANCE_MODE=github
GOVERNANCE_REPO_URL=https://github.com/your-org/govern-mcp
GITHUB_TOKEN=ghp_...
CACHE_TTL_SECONDS=300
```

Add a webhook in GitHub repo settings → `POST https://your-server/webhook/github` to invalidate the cache on every push to main.

## Running compliance checks

```bash
cd mcp-server

# All @enforced scenarios (CI)
.venv/bin/behave --tags=enforced

# All scenarios including @wip (local exploration)
.venv/bin/behave --no-skipped

# Unit tests
.venv/bin/pytest tests/ -q
```

## CLI validator

```bash
cd mcp-server

# Validate topic names
.venv/bin/governance-validate topic raw.sales.pos.hmsu.commons.guestcheck.v1

# Validate an RBAC binding
.venv/bin/governance-validate rbac DeveloperRead topic "raw.sales.*"

# Validate a service account name
.venv/bin/governance-validate sa sa-sales-lsretail-lookup-connector-source-jdbc-dev
```

Exit code 0 = valid, 1 = errors. Suitable for use as a pre-commit hook or in CI.

## ADRs in this template

| # | Title | Status |
|---|---|---|
| 001 | Kafka topic naming | Accepted |
| 002 | Consumer group naming | Accepted |
| 003 | KStreams state store naming | Accepted |
| 004 | Camel route naming | Draft |
| 005 | SpringBoot required config | Draft |
| 006 | Helm resource standards | Draft |
| 007 | Schema Registry conventions | Accepted |
| 008 | Confluent auth strategy | Accepted |
| 009 | Connector SA naming and lifecycle | Accepted |
| 010 | Two-repo Terraform separation | Accepted |
| 011 | Per-domain semver deploy tags | Accepted |

Replace or extend these with your own decisions. The ADR format is standard Markdown with a frontmatter block — see any file in `adrs/global/` for the structure.
