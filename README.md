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
| `validate_topic_name(name, team?)` | Validate topic name against governance.yml |
| `validate_rbac_binding(role, type, name, team?)` | Validate an RBAC binding |
| `validate_sa_name(name, team?)` | Validate a service account name |
| `validate_schema_entry(format, compatibility_level, team?)` | Validate a Schema Registry entry |
| `validate_rest_path(path, team?)` | Validate a REST API path |
| `validate_service_name(name, team?)` | Validate a microservice name |
| `get_rollout_status(rule_name)` | Query canary rollout phase for a rule |

All `validate_*` tools accept an optional `team` parameter. When the rule is in `canary` phase, canary teams receive errors; all other teams receive a warning instead (`valid: true`). Omitting `team` is treated as "not in canary" (advisory warning).

`rule_name` for `get_rollout_status` is one of: `kafka.topic`, `kafka.rbac`, `kafka.service_account`, `kafka.schema_registry`, `rest_api`, `service`.

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
| `/webhook/incident` | POST | Report a violation → opens a PR against the governance repo |

---

## Webhooks

### `POST /webhook/incident` — Incident-to-Eval Synthesis

When a governance violation reaches production (caught by CI, a pre-commit hook, or a manual report), call this endpoint to automatically synthesise it into a new entry in `knowledge/failures.md` in the governance repo. The entry is submitted as a pull request so it can be reviewed before becoming visible to agents.

**Required environment variables:**

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | Personal access token with `repo` scope. **Endpoint returns 503 if absent (fail-closed).** |
| `NOMOS_REPO_PATH` | `{owner}/{repo}` of the governance repo, e.g. `my-org/governance`. Falls back to `GOVERNANCE_REPO_URL` in GitHub mode. |

**Request body:**

```json
{
  "resource_name":   "raw.payments.checkout.v1",
  "resource_type":   "kafka_topic",
  "rule_violated":   "Topic must have exactly 7 dot-separated segments",
  "bad_pattern":     "raw.payments.checkout.v1",
  "correct_pattern": "raw.payments.pos.acme.checkout.receipt.v1"
}
```

**Response (200):**

```json
{
  "queued": true,
  "pr_url": "https://github.com/my-org/governance/pull/7",
  "entry_preview": "\n## Topic must have exactly 7 ...\n\n- **Resource:** ..."
}
```

**Error responses:**

| Status | Cause |
|---|---|
| 400 | Missing or malformed fields in the request body |
| 503 | `GITHUB_TOKEN` or `NOMOS_REPO_PATH` not configured |
| 502 | GitHub API unreachable or returned an error |

**Example — report from a GitHub Actions CI failure:**

```yaml
- name: Report governance violation
  if: failure()
  run: |
    curl -sX POST https://nomos.acme.com/webhook/incident \
      -H "Content-Type: application/json" \
      -d '{
        "resource_name":   "${{ env.RESOURCE_NAME }}",
        "resource_type":   "${{ env.RESOURCE_TYPE }}",
        "rule_violated":   "${{ env.RULE_VIOLATED }}",
        "bad_pattern":     "${{ env.BAD_PATTERN }}",
        "correct_pattern": "${{ env.CORRECT_PATTERN }}"
      }'
```

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

## Canary Rollout

Rule changes can be rolled out gradually to specific teams before they are enforced for everyone. Add a `rollout:` block to any rule section in `governance.yml`:

```yaml
kafka:
  topic:
    segment_count: 7
    prefixes: [raw, public, ready, private, dev]
    rollout:
      phase: canary          # canary | stable
      teams:
        - payments           # these teams receive errors on violation
        - platform           # all other teams receive a warning instead
```

**Behaviour by phase:**

| Phase | Canary team | Non-canary team | No team supplied |
|---|---|---|---|
| `stable` (default) | error | error | error |
| `canary` | error | warning (`valid: true`) | warning (`valid: true`) |

When a rule is in canary and the team is not in the list, `validate_*` returns:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "[canary rollout] expected 7 dot-separated segments, got 3",
    "rule is in canary rollout, not yet enforced for team 'fulfillment' (enforced for: payments, platform)"
  ]
}
```

Use `get_rollout_status(rule_name)` to discover the current phase before validating:

```json
{ "rule_name": "kafka.topic", "phase": "canary", "teams": ["payments", "platform"], "enforced_for_all": false }
```

**Rollout lifecycle:**

```
1. Add rollout: {phase: canary, teams: [team-a]}   ← test with pilot team
2. Expand teams list as teams adopt the rule
3. Set phase: stable (or remove rollout block)     ← enforce for all
```

The `team` parameter can be passed explicitly to all `validate_*` MCP tools and REST endpoints (`"team": "payments"` in the JSON body). When calling via `/teams/<team>/mcp`, the team is resolved automatically from the URL.

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
