# nomos

> Constitutional Governance server — exposes ADRs, constitutions, naming conventions, and executable compliance checks via MCP, REST, and CLI.

Part of the [Constitutional Governance](https://github.com/your-org/constitutional-governance) methodology.

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
nomos --github https://github.com/your-org/your-governance-repo
```

Use [nomos-template](https://github.com/your-org/nomos-template) as your governance repo starting point.

---

## What it exposes

### MCP tools (Claude Code, Cursor, Windsurf, and any MCP-compatible agent)

Connect via `http://your-server/mcp`. Configure with `nomos install-hooks --tool mcp`.

```
# Discovery
list_constitutions()              → ["global", "kafka", "camel", "springboot"]
list_check_domains()              → ["kafka", "springboot", ...]
list_knowledge()                  → ["failures", "successful"]

# Rules and conventions
get_active_rules()                → full governance.yml as structured object
get_constitution("kafka")         → domain principles and invariants
get_kafka_conventions()           → prefixes, roles, patterns, prefix semantics
get_knowledge("failures")         → platform-specific AI failure patterns

# ADRs
list_adrs()                       → [{id, title, status}, ...]
get_adr("001")                    → full ADR content
search_adrs("consumer group")     → ADRs matching the query

# Checks
get_checks("kafka")               → [{title, status, content}, ...]

# Validation — call these after generating resources, before proposing
validate_topic_name("...")        → {valid, errors, warnings}
validate_rbac_binding(...)        → {valid, errors}
validate_sa_name("...")           → {valid, errors}
validate_schema_entry("AVRO", "BACKWARD")  → {valid, errors, warnings}
validate_rest_path("/v1/orders")  → {valid, errors, warnings}
validate_service_name("...")      → {valid, errors, warnings}
```

**Recommended workflow for agents:** call `get_knowledge("failures")` first, then generate, then validate.

### CLI (GitHub Copilot and any tool with terminal access)

`nomos-validate` is the model-agnostic alternative to MCP. Any agent that can run shell commands uses it directly — no server connection required for local mode.

Configure with `nomos install-hooks --tool copilot` — generates `.github/copilot-instructions.md` with the CLI validation workflow.

### REST endpoints (for CI and scripts)

```
GET  /health
POST /validate/topic        {"name": "raw.payments.v1"}
POST /validate/rbac         {"role_name": "...", "resource_type": "...", "resource_name": "..."}
POST /validate/sa           {"name": "sa-payments-connector-source-jdbc-prod"}
POST /validate/schema       {"format": "AVRO", "compatibility_level": "BACKWARD"}
POST /validate/rest-path    {"path": "/v1/orders/{orderId}/items"}
POST /validate/service-name {"name": "retail-order-api"}
POST /webhook/github        (GitHub push webhook — invalidates cache)
```

### CLI commands

**Validate resources** (local or against a shared server):

```bash
nomos-validate topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate rbac DeveloperRead topic "raw.payments.*"
nomos-validate sa "sa-payments-connector-source-jdbc-prod"
nomos-validate schema AVRO BACKWARD
nomos-validate rest-path "/v1/orders/{orderId}/items"
nomos-validate service-name "retail-order-api"

# Against a shared server (no local files needed — works from any tool)
nomos-validate --server https://governance.acme.com topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate --server https://governance.acme.com rest-path "/v1/orders"
nomos-validate --server https://governance.acme.com service-name "retail-order-api"
```

**Governance tooling**:

```bash
# Install config for all tools (MCP + Copilot) + pre-commit hook
nomos install-hooks --server https://governance.acme.com

# MCP-compatible agents only (Claude Code, Cursor, Windsurf, ...)
nomos install-hooks --server https://governance.acme.com --tool mcp

# GitHub Copilot only (.github/copilot-instructions.md)
nomos install-hooks --server https://governance.acme.com --tool copilot

# Scaffold a new domain (constitution + ADR + Gherkin template)
nomos scaffold domain kafka

# Verify a @wip scenario is ready to promote to @enforced
nomos check-promotion features/kafka/topic-naming.feature --run
```

---

## Usage examples

### 1. Kafka / Terraform repo (infrastructure team)

Add to your repo's `CLAUDE.md`:

```markdown
## Before generating any HCL

**Step 1 — Load rules (call once per task):**
get_knowledge("failures")      ← read platform AI failure patterns first
get_kafka_conventions()        ← topic naming, RBAC roles, prefix semantics
get_constitution("kafka")      ← invariants, connector RBAC patterns, SA rules

**Step 2 — Self-validate before proposing:**
validate_topic_name(name)                        ← for every topic key
validate_rbac_binding(role, resource_type, name) ← for every role binding
validate_sa_name(name)                           ← for every service account
validate_schema_entry(format, compatibility)     ← for every schema entry
```

Wire up the pre-commit hook so humans are also covered:

```bash
nomos install-hooks --server https://governance.your-org.com
```

### 2. REST API service repo

**MCP agents** (Claude Code, Cursor, ...) — add to your instruction file (`CLAUDE.md`, `AGENTS.md`, etc.):

```markdown
## Before adding or modifying REST endpoints

get_knowledge("failures")      ← read platform AI failure patterns first
get_rest_conventions()         ← URL patterns, method semantics, versioning rules
get_constitution("rest-api")   ← error format, pagination, ID conventions

validate_rest_path(path)       ← for every new endpoint path
validate_service_name(name)    ← when naming a new service or Helm release
```

**Copilot and other tools** — use the CLI from the terminal:

```bash
nomos-validate --server https://governance.your-org.com rest-path "/v1/customer-orders/{orderId}/line-items"
nomos-validate --server https://governance.your-org.com service-name "retail-order-api"
```

Example validation output:

```
ERR /v1/CustomerOrders
    path must be lowercase — use kebab-case for all static segments

OK  /v1/customer-orders/{orderId}/line-items
```

### 3. Onboarding a new service repo

One command configures all supported AI tools:

```bash
cd /path/to/your-service-repo
nomos install-hooks --server https://governance.your-org.com
```

This creates:
- `.mcp.json` — MCP config for Claude Code, Cursor, Windsurf, and other MCP agents
- `.github/copilot-instructions.md` — custom instructions for GitHub Copilot (REST API workflow)
- `.git/hooks/pre-commit` — validates staged resources before every commit (model-agnostic)

For MCP-compatible agents, add an instruction file (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, etc.) depending on your tool:

```markdown
## Governance

This repo is connected to the platform governance server via `.mcp.json`.

Before generating or modifying resources:
1. get_knowledge("failures")     ← always call this first
2. get_constitution("global")    ← platform-wide principles
3. get_constitution("<domain>")  ← domain-specific rules (kafka, rest-api, ...)
4. validate_*                    ← self-validate before returning output
```

For Copilot and other non-MCP tools, `.github/copilot-instructions.md` (generated above) contains the equivalent workflow using `nomos-validate` from the terminal.

---

## Deployment

The platform team deploys **one** shared instance. Every team delegates to it — nobody runs their own copy.

```bash
# Docker (recommended for production)
export GOVERNANCE_REPO_URL=https://github.com/your-org/your-governance-repo
export GITHUB_TOKEN=ghp_...
docker compose up -d
```

Full deployment guide: [nomos-template/DEPLOYMENT.md](https://github.com/your-org/nomos-template/blob/main/DEPLOYMENT.md)

---

## Server flags

```
nomos --repo PATH          Load governance repo from local path
nomos --github URL         Load governance repo from GitHub (requires GITHUB_TOKEN for private repos)
nomos --host HOST          Bind host (default: 127.0.0.1; use 0.0.0.0 in Docker)
nomos --port PORT          Listen port (default: 8080)
```

Environment variables: `GOVERNANCE_REPO_PATH`, `GOVERNANCE_REPO_URL`, `GITHUB_TOKEN`, `GITHUB_BRANCH`, `CACHE_TTL_SECONDS`, `LOG_LEVEL`.

---

## Contributing

→ [CONTRIBUTING.md](https://github.com/your-org/constitutional-governance/blob/main/.github/CONTRIBUTING.md)
