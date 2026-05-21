# nomos

> Constitutional Governance server — serves platform rules to AI agents via MCP and CLI.

Part of the [Constitutional Governance](https://github.com/constitutional-governance/constitutional-governance) methodology.

---

## Install

```bash
pip install nomos
```

---

## Quick start

```bash
# Point at a governance repo and start the server
nomos --repo /path/to/your-governance-repo
# → listening on http://127.0.0.1:8080

# Or load from GitHub directly
nomos --github https://github.com/constitutional-governance/nomos-template
```

Use [nomos-template](https://github.com/constitutional-governance/nomos-template) as your governance repo starting point.

---

## Integration paths

Nomos exposes governance rules through two interfaces. Choose based on your tooling:

| Interface | When to use | How to configure |
|---|---|---|
| **MCP** | Interactive AI agents — Claude Code, Copilot, Cursor, Windsurf | `nomos install-hooks` |
| **CLI** | Pre-commit hooks, CI pipelines, scripts, agents without MCP | `pip install nomos` |

Both interfaces read the same governance rules from the same server. The CLI can run in local mode (no server needed) or remote mode (delegates to a shared server).

---

## MCP interface

For AI agents that support the Model Context Protocol.

### Setup

```bash
# Generates .mcp.json (Claude Code) + .vscode/mcp.json (VS Code / Copilot)
nomos install-hooks --server https://governance.your-org.com

# Claude Code only
nomos install-hooks --server https://governance.your-org.com --tool claude

# VS Code / GitHub Copilot only
nomos install-hooks --server https://governance.your-org.com --tool vscode
```

### Available tools

```
# Discovery
list_constitutions()              → ["global", "kafka", "rest-api", ...]
list_check_domains()              → ["kafka", "springboot", ...]
list_knowledge()                  → ["failures", "successful"]

# Rules and conventions
get_active_rules()                → full governance.yml as structured object
get_constitution("kafka")         → domain principles and invariants
get_kafka_conventions()           → prefixes, roles, patterns, prefix semantics
get_rest_conventions()            → URL patterns, method semantics, versioning rules
get_service_conventions()         → service naming, k8s constraints
get_knowledge("failures")         → platform-specific AI failure patterns

# ADRs
list_adrs()                       → [{id, title, status}, ...]
get_adr("001")                    → full ADR content
search_adrs("consumer group")     → ADRs matching the query

# Checks
get_checks("kafka")               → [{title, status, content}, ...]

# Validation
validate_topic_name("...")        → {valid, errors, warnings}
validate_rbac_binding(...)        → {valid, errors}
validate_sa_name("...")           → {valid, errors}
validate_schema_entry("AVRO", "BACKWARD")  → {valid, errors, warnings}
validate_rest_path("/v1/orders")  → {valid, errors, warnings}
validate_service_name("...")      → {valid, errors, warnings}
```

**Recommended agent workflow:** call `get_knowledge("failures")` first, then generate, then validate.

---

## CLI interface

For pre-commit hooks, CI pipelines, and any tool that can run a shell command.

### Validate resources

```bash
# Local mode — reads governance.yml from GOVERNANCE_REPO_PATH
nomos-validate topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate rbac DeveloperRead topic "raw.payments.*"
nomos-validate sa "sa-payments-connector-source-jdbc-prod"
nomos-validate schema AVRO BACKWARD
nomos-validate rest-path "/v1/orders/{orderId}/items"
nomos-validate service-name "retail-order-api"

# Remote mode — delegates to a shared server, no local files needed
nomos-validate --server https://governance.your-org.com topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate --server https://governance.your-org.com rbac DeveloperRead topic "raw.payments.*"
nomos-validate --server https://governance.your-org.com rest-path "/v1/orders"
nomos-validate --server https://governance.your-org.com service-name "retail-order-api"
```

Exit code `0` = valid. Exit code `1` = invalid — read the output and fix before committing.

### Example output

```
OK  raw.payments.pos.checkout.receipts.transaction.v1

ERR raw.payments.pos.checkout.v1
    expected 7 dot-separated segments, got 5

OK  /v1/orders/{orderId}/items

ERR /v1/CustomerOrders
    path must be lowercase — use kebab-case for all static segments
```

### Pre-commit hook

`nomos install-hooks` installs a pre-commit hook that validates staged files automatically:

```bash
nomos install-hooks --server https://governance.your-org.com
```

The hook runs `nomos-validate` on every commit — no MCP, no server connection needed for local validation.

### Governance tooling

```bash
# Scaffold a new domain (constitution + ADR + Gherkin template)
nomos scaffold domain rest-api

# Verify a @wip scenario is ready to promote to @enforced
nomos check-promotion features/kafka/topic-naming.feature --run
```

---

## GitHub Copilot Extension

Exposes Nomos as a `@nomos` agent in any Copilot-enabled client (VS Code, GitHub.com, mobile).

```
@nomos validate topic raw.payments.pos.checkout.receipts.transaction.v1
@nomos validate rbac DeveloperRead topic "raw.payments.*"
@nomos get kafka conventions
@nomos get constitution kafka
@nomos list adrs
@nomos get adr 001
@nomos search adrs consumer group
```

### Setup

1. Create a GitHub App at **github.com/settings/apps/new**
2. Under **Copilot Extension**, set the agent URL to `https://governance.your-org.com/copilot/agent`
3. Install the app in your organisation
4. Developers can invoke `@nomos` in any Copilot chat

No separate deployment needed — the same Nomos server that serves MCP also handles Copilot Extension requests at `POST /copilot/agent`.

---

## REST endpoints

For CI pipelines and scripts that prefer HTTP over CLI:

```
GET  /health
POST /validate/topic        {"name": "raw.payments.v1"}
POST /validate/rbac         {"role_name": "...", "resource_type": "...", "resource_name": "..."}
POST /validate/sa           {"name": "sa-payments-connector-source-jdbc-prod"}
POST /validate/schema       {"format": "AVRO", "compatibility_level": "BACKWARD"}
POST /validate/rest-path    {"path": "/v1/orders/{orderId}/items"}
POST /validate/service-name {"name": "retail-order-api"}
POST /webhook/github        (GitHub push webhook — invalidates cache)
POST /copilot/agent         (GitHub Copilot Extension — SSE agent protocol)
```

---

## Usage examples

### 1. Kafka / Terraform repo

Add to your agent instruction file (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`):

```markdown
## Before generating any HCL

1. get_knowledge("failures")      ← read platform AI failure patterns first
2. get_kafka_conventions()        ← topic naming, RBAC roles, prefix semantics
3. get_constitution("kafka")      ← invariants, connector RBAC patterns, SA rules
4. [generate]
5. validate_topic_name / validate_rbac_binding / validate_sa_name / validate_schema_entry
```

Install the pre-commit hook so humans are covered too:

```bash
nomos install-hooks --server https://governance.your-org.com
```

### 2. REST API service repo

```markdown
## Before adding or modifying REST endpoints

1. get_knowledge("failures")
2. get_rest_conventions()
3. get_constitution("rest-api")
4. [generate]
5. validate_rest_path / validate_service_name
```

### 3. Onboarding a new repo

```bash
cd /path/to/your-service-repo
nomos install-hooks --server https://governance.your-org.com
```

Generates:
- `.mcp.json` — Claude Code
- `.vscode/mcp.json` — VS Code / GitHub Copilot
- `.git/hooks/pre-commit` — CLI validation on every commit

---

## Deployment

The platform team deploys **one** shared instance. Every repo delegates to it.

```bash
export GOVERNANCE_REPO_URL=https://github.com/constitutional-governance/nomos-template
export GITHUB_TOKEN=ghp_...
docker compose up -d
```

---

## Server flags

```
nomos --repo PATH          Load governance repo from local path
nomos --github URL         Load governance repo from GitHub
nomos --host HOST          Bind host (default: 127.0.0.1; use 0.0.0.0 in Docker)
nomos --port PORT          Listen port (default: 8080)
```

Environment variables: `GOVERNANCE_REPO_PATH`, `GOVERNANCE_REPO_URL`, `GITHUB_TOKEN`, `GITHUB_BRANCH`, `CACHE_TTL_SECONDS`, `LOG_LEVEL`.

---

## Contributing

→ [CONTRIBUTING.md](https://github.com/constitutional-governance/constitutional-governance/blob/main/.github/CONTRIBUTING.md)
