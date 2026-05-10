# Nomos

> *The reference implementation of [Constitutional Governance](https://github.com/your-org/constitutional-governance).*

Nomos is an open-source governance server for engineering platforms. It exposes your organization's rules — naming conventions, RBAC constraints, architectural decisions — as MCP tools queryable by AI agents, as a CLI for pre-commit hooks, and as an executable Gherkin suite for CI pipelines.

**The agent is not unintelligent. It is uninformed.** Nomos changes that.

---

## What it does

| Interface | Use case |
|---|---|
| **MCP tools** | AI agents query rules before and during code generation |
| **CLI (`nomos-validate`)** | Pre-commit hooks validate names and bindings locally |
| **Gherkin suite** | CI pipeline verifies compliance on every pull request |

All three interfaces read the same source: your `governance.yml` and the Markdown files in this repo.

---

## Repository layout

```
nomos/
├── governance.yml          ← the only file most teams need to edit
├── constitution.md         ← platform-wide principles
├── constitutions/          ← per-domain principles (kafka.md, camel.md, ...)
├── adrs/                   ← Architecture Decision Records
│   └── global/
├── mcp-server/             ← the server (Python, FastMCP)
│   ├── src/
│   │   ├── server.py       ← MCP tool definitions
│   │   ├── validators/     ← topic, RBAC, SA naming validators
│   │   ├── loaders/        ← local filesystem and GitHub API loaders
│   │   └── models/         ← Pydantic config and response models
│   ├── features/           ← Gherkin scenarios (executable checks)
│   └── tests/              ← pytest unit tests
└── setup.sh                ← bootstrap script
```

---

## Getting started

```bash
git clone https://github.com/your-org/nomos
cd nomos
./setup.sh
```

Edit `governance.yml` to match your naming conventions and RBAC roles. Then start the server:

```bash
cd mcp-server
.venv/bin/nomos
# → listening on http://127.0.0.1:8080
```

Connect it to Claude Code — add `.mcp.json` at your project root:

```json
{
  "mcpServers": {
    "nomos": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

---

## MCP tools

| Tool | Purpose |
|---|---|
| `list_constitutions()` | Discover what domains are governed |
| `list_check_domains()` | Discover what domains have executable checks |
| `get_active_rules()` | Inspect the full governance.yml in effect |
| `get_constitution(domain)` | Domain principles — read before architectural decisions |
| `get_kafka_conventions()` | Topic naming, RBAC, schema subjects, consumer groups |
| `get_camel_conventions()` | Route IDs, application names, base class, BOM |
| `get_naming_conventions(type)` | Pattern + examples for one resource type |
| `get_adr(id)` | Full ADR content by ID |
| `search_adrs(query)` | Full-text search across ADRs |
| `list_adrs()` | All governance decisions at a glance |
| `get_checks(domain)` | Gherkin checks for a domain |
| `get_helm_template(service_type)` | Ready-to-use Helm values template |
| `validate_topic_name(name)` | Validate against governance.yml rules |
| `validate_rbac_binding(role, type, name)` | Validate an RBAC binding |
| `validate_sa_name(name)` | Validate a service account name |

---

## Customizing for your organization

`governance.yml` drives all validators. Edit it to reflect your platform:

```yaml
project:
  name: "My Platform Governance"

kafka:
  topic:
    segment_count: 7
    prefixes: [raw, public, ready, private, kstreams, sink, dev]
    max_length: 249
  rbac:
    valid_roles: [DeveloperRead, DeveloperWrite, ResourceOwner]
    admin_roles: [DeveloperManage]
    admin_resource_types: [cluster]
  service_account:
    prefix: "sa-"
    valid_envs: [dev, staging, prod]
    connector_directions: [source, sink]

camel:
  base_class: "com.yourorg.camel.BaseRouteBuilder"
  parent_bom: "com.yourorg:camel-starter-parent:3.7.2"
```

The constitutions and ADRs are plain Markdown — edit or replace them with your organization's decisions.

---

## Running in production (GitHub mode)

Point Nomos at your governance repo on GitHub so the entire organization gets live updates:

```bash
# mcp-server/.env
GOVERNANCE_MODE=github
GOVERNANCE_REPO_URL=https://github.com/your-org/your-governance-repo
GITHUB_TOKEN=ghp_...
CACHE_TTL_SECONDS=300
```

Add a webhook in GitHub → `POST https://your-nomos-server/webhook/github` to invalidate the cache on push to main.

---

## Running checks

```bash
cd mcp-server

# All @enforced scenarios — suitable for CI
.venv/bin/behave --tags=enforced

# All scenarios including @wip — local exploration
.venv/bin/behave --no-skipped

# Unit tests
.venv/bin/pytest tests/ -q
```

## CLI validator

```bash
# Validate topic names (exit 0 = valid, 1 = errors)
.venv/bin/nomos-validate topic acme.payments.checkout.team.receipts.transaction.v1

# Validate an RBAC binding
.venv/bin/nomos-validate rbac DeveloperRead topic "acme.payments.*"

# Validate a service account name
.venv/bin/nomos-validate sa sa-payments-connector-source-jdbc-prod
```

Use `nomos-validate` as a pre-commit hook to catch violations before they reach CI.

---

## The delegation model

Teams do not copy governance rules. They delegate to a single Nomos instance operated by the platform team. When a rule changes, it changes once and every agent, hook, and pipeline sees the update immediately.

```
platform-governance-repo  ←  rules live here
        │
        ▼
    Nomos server          ←  exposes rules as MCP tools + CLI
        │
   ┌────┴────┐
   ▼         ▼
AI agents  CI pipeline  ←  both query the same rules
```

This is the core principle of Constitutional Governance: **delegation over distribution**.

---

## ADRs included in this template

| # | Title | Status |
|---|---|---|
| 001 | Kafka topic naming | Accepted |
| 002 | Consumer group naming | Accepted |
| 007 | Schema Registry conventions | Accepted |

Replace or extend these with your organization's architectural decisions.

---

## Contributing

Nomos is the reference implementation of Constitutional Governance. Contributions are welcome.

- Bug reports and feature requests: open an issue
- The methodology itself: contribute to [constitutional-governance](https://github.com/your-org/constitutional-governance)
- Implementations in other stacks: document them in the constitutional-governance repo

---

## License

Apache 2.0
