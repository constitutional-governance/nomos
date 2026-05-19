# Nomos

> Constitutional Governance server — the reference implementation of [Constitutional Governance](https://github.com/your-org/constitutional-governance).

```bash
pip install nomos
nomos --repo /path/to/your-governance-repo
```

Nomos exposes your governance rules as MCP tools queryable by AI agents, as a REST API for pre-commit hooks, and runs your Gherkin compliance checks in CI.

**Looking for the governance template?** → [nomos-template](https://github.com/your-org/nomos-template)

---

## How it works

Nomos reads a governance repository — a directory containing a `governance.yml`, constitutions, ADRs, and Gherkin feature files — and exposes its rules through three interfaces:

| Interface | Use case |
|---|---|
| **MCP** (`/mcp`) | AI agents query rules before and during code generation |
| **REST** (`/validate/*`) | CLI pre-commit hooks validate names without local files |
| **Gherkin** (`behave --tags=enforced`) | CI pipeline verifies compliance on every PR |

---

## Quick start

```bash
# Install
pip install nomos

# Point at your governance repo
nomos --repo /path/to/governance-repo
# → listening on http://127.0.0.1:8080

# Or use the nomos-template as your starting point:
# https://github.com/your-org/nomos-template
```

Connect an AI agent — add `.mcp.json` to your project:

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

## CLI

```bash
# Start the server
nomos --repo /path/to/governance-repo
nomos --repo . --port 9090
nomos --github https://github.com/your-org/governance-repo   # GitHub mode

# Validate resources (local mode)
nomos-validate topic raw.payments.pos.checkout.receipts.transaction.v1
nomos-validate rbac DeveloperRead topic "raw.payments.*"
nomos-validate sa sa-payments-connector-source-jdbc-prod
nomos-validate schema AVRO BACKWARD

# Validate resources (remote mode — delegates to shared server)
nomos-validate --server https://governance.acme.com topic raw.payments...
nomos-validate --server https://governance.acme.com schema AVRO BACKWARD_TRANSITIVE

# Install .mcp.json + pre-commit hook in a project repo
nomos install-hooks --server https://governance.acme.com --project-dir /path/to/repo
```

---

## MCP tools

### Discovery and conventions

| Tool | Purpose |
|---|---|
| `list_constitutions()` | Discover governed domains |
| `list_check_domains()` | Discover domains with executable checks |
| `list_knowledge()` | Discover available knowledge topics (failures, lessons learned) |
| `get_active_rules()` | Full governance.yml as structured object |
| `get_constitution(domain)` | Domain principles — `"global"`, `"kafka"`, etc. |
| `get_kafka_conventions()` | Topic naming, RBAC, schema subjects, consumer groups, prefix semantics |
| `get_camel_conventions()` | Route IDs, application names, base class, BOM |
| `get_naming_conventions(type)` | Pattern + examples for one resource type |
| `get_knowledge(topic)` | Knowledge documents — call `get_knowledge("failures")` before generating resources |

### ADRs and checks

| Tool | Purpose |
|---|---|
| `get_adr(id)` | Full ADR content |
| `search_adrs(query)` | Full-text search across ADRs |
| `list_adrs()` | All governance decisions |
| `get_checks(domain)` | Gherkin checks for a domain |
| `get_helm_template(service_type)` | Helm values template |

### Validation

| Tool | Purpose |
|---|---|
| `validate_topic_name(name)` | Validate topic name against governance.yml |
| `validate_rbac_binding(role, type, name)` | Validate an RBAC binding |
| `validate_sa_name(name)` | Validate a service account name |
| `validate_schema_entry(format, compatibility_level)` | Validate a Schema Registry entry |

### Recommended agent workflow

Before generating any resource:
1. Call `get_knowledge("failures")` — reads platform-specific AI failure patterns
2. Call `get_kafka_conventions()` or `get_constitution("kafka")` — loads current rules
3. Generate the resource
4. Call the relevant `validate_*` tool — self-validate before proposing

## REST endpoints

| Endpoint | Method | Body |
|---|---|---|
| `/health` | GET | — |
| `/validate/topic` | POST | `{"name": "..."}` |
| `/validate/rbac` | POST | `{"role_name": "...", "resource_type": "...", "resource_name": "..."}` |
| `/validate/sa` | POST | `{"name": "..."}` |
| `/validate/schema` | POST | `{"format": "AVRO", "compatibility_level": "BACKWARD"}` |
| `/webhook/github` | POST | Invalidates cache on push |

---

## Deploying a shared instance

```bash
export GOVERNANCE_REPO_URL=https://github.com/your-org/governance-repo
export GITHUB_TOKEN=ghp_...
docker compose up -d
```

See `docker-compose.yml` (GitHub mode) and `docker-compose.local.yml` (filesystem mount).

---

## Governance repo structure

Nomos expects this layout in the governance repo:

```
governance-repo/
├── governance.yml          ← drives all validators (prefixes, roles, SA envs, schema formats)
├── constitution.md         ← global principles
├── constitutions/
│   └── <domain>.md         ← per-domain principles (kafka, camel, springboot, …)
├── knowledge/
│   ├── failures.md         ← systematic AI failure patterns for this platform
│   └── successful.md       ← patterns and approaches that have worked well
├── adrs/
│   └── global/
│       └── NNN-title.md    ← Architecture Decision Records
└── features/
    └── <domain>/
        └── *.feature       ← Gherkin checks (@enforced / @wip)
```

Use [nomos-template](https://github.com/your-org/nomos-template) as your starting point.

---

## Examples

The `examples/` directory contains a complete Kafka governance setup that can be used as a governance repo directly:

```bash
nomos --repo examples/kafka
```

---

## Development

```bash
git clone https://github.com/your-org/nomos
cd nomos/mcp-server
python -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Tests
.venv/bin/pytest tests/ -q

# Gherkin against the built-in Kafka example
GOVERNANCE_REPO_PATH=../examples/kafka .venv/bin/behave --tags=enforced
```

---

## License

Apache 2.0
