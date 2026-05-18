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

### MCP tools (for AI agents)

Connect any MCP-compatible agent (Claude Code, etc.) to `http://your-server/mcp`:

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
```

**Recommended workflow for agents:** call `get_knowledge("failures")` first, then generate, then validate.

### REST endpoints (for CI and scripts)

```
GET  /health
POST /validate/topic      {"name": "raw.payments.v1"}
POST /validate/rbac       {"role_name": "...", "resource_type": "...", "resource_name": "..."}
POST /validate/sa         {"name": "sa-payments-connector-source-jdbc-prod"}
POST /validate/schema     {"format": "AVRO", "compatibility_level": "BACKWARD"}
POST /webhook/github      (GitHub push webhook — invalidates cache)
```

### CLI commands

**Validate resources** (local or against a shared server):

```bash
nomos-validate topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate rbac DeveloperRead topic "raw.payments.*"
nomos-validate sa "sa-payments-connector-source-jdbc-prod"
nomos-validate schema AVRO BACKWARD

# Against a shared server (no local files needed)
nomos-validate --server https://governance.acme.com topic "raw.payments.pos.checkout.receipts.transaction.v1"
nomos-validate --server https://governance.acme.com schema AVRO BACKWARD_TRANSITIVE
```

**Governance tooling**:

```bash
# Install .mcp.json + pre-commit hook in a project repo
nomos install-hooks --server https://governance.acme.com

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

Add to your repo's `CLAUDE.md`:

```markdown
## Before adding or modifying REST endpoints

get_knowledge("failures")      ← read platform AI failure patterns first
get_rest_conventions()         ← URL patterns, method semantics, versioning rules
get_constitution("rest-api")   ← error format, pagination, ID conventions

validate_rest_path(path)       ← for every new endpoint path
validate_service_name(name)    ← when naming a new service or Helm release
```

Example agent session:

```
→ get_rest_conventions()
  path_pattern: /v{n}/{resource}[/{id}[/{sub-resource}]]
  versioning_strategy: path
  method_semantics: { GET: "read, idempotent", POST: "create", ... }

→ validate_rest_path("/v1/CustomerOrders")
  valid: false
  errors: ["path must be lowercase — use kebab-case for all static segments"]

→ validate_rest_path("/v1/customer-orders")
  valid: true
  warnings: ["segment 'customer-orders' looks like a singular noun — ..."]

→ validate_rest_path("/v1/customer-orders/{orderId}/line-items")
  valid: true
```

### 3. Onboarding a new service repo

One command installs the `.mcp.json` and pre-commit hook:

```bash
cd /path/to/your-service-repo
nomos install-hooks --server https://governance.your-org.com
```

This creates:
- `.mcp.json` — points Claude Code at the governance server
- `.git/hooks/pre-commit` — validates staged resources before every commit

For the agent workflow, add a minimal `CLAUDE.md`:

```markdown
## Governance

This repo is connected to the platform governance server via `.mcp.json`.

Before generating or modifying resources:
1. get_knowledge("failures")     ← always call this first
2. get_constitution("global")    ← platform-wide principles
3. get_constitution("<domain>")  ← domain-specific rules (kafka, rest-api, ...)
4. validate_*                    ← self-validate before returning output
```

Call `list_constitutions()` and `list_check_domains()` to discover what's available in the connected governance repo.

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
