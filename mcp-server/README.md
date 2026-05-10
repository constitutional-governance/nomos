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
list_constitutions()           → ["global", "kafka", "camel", "springboot"]
get_constitution("kafka")      → domain principles and invariants
list_adrs()                    → [{id, title, status}, ...]
get_adr("001")                 → full ADR content
search_adrs("consumer group")  → ADRs matching the query
get_kafka_conventions()        → prefixes, roles, patterns
validate_topic_name("...")     → {valid, errors, warnings}
validate_rbac_binding(...)     → {valid, errors}
validate_sa_name("...")        → {valid, errors}
get_checks("kafka")            → [{title, status, path}, ...]
get_active_rules()             → full governance.yml as structured object
```

### REST endpoints (for CI and scripts)

```
GET  /health
POST /validate/topic      {"name": "raw.payments.v1"}
POST /validate/rbac       {"role_name": "...", "resource_type": "...", "resource_name": "..."}
POST /validate/sa         {"name": "sa-payments-connector-source-jdbc-prod"}
POST /webhook/github      (GitHub push webhook — invalidates cache)
```

### CLI commands

**Validate resources** (local or against a shared server):

```bash
nomos-validate topic "raw.payments.checkout.v1"
nomos-validate rbac DeveloperRead topic "raw.payments.*"
nomos-validate sa "sa-payments-connector-source-jdbc-prod"

# Against a shared server (no local files needed)
nomos-validate --server https://governance.acme.com topic "raw.payments.v1"
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
