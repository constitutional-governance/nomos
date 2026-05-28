# govern-mcp

Nomos — the Constitutional Governance server. Exposes governance rules via MCP, REST, and CLI so AI agents can query conventions and validate resources before generating code.

**Read README.md before starting any work.** It documents the MCP tools, REST endpoints, recommended agent workflow, and failure modes.

---

## Architecture

```
mcp-server/
├── src/
│   ├── tools/              ← MCP tool definitions (get_conventions, validate_*, rollout)
│   │   ├── knowledge_tools.py
│   │   └── rollout_tools.py
│   ├── validators/         ← Validation logic, one file per resource type
│   │   ├── rollout.py      ← apply_rollout() — pure function, shared by all validators
│   │   ├── topic.py
│   │   ├── rbac.py
│   │   ├── sa_naming.py
│   │   ├── schema.py
│   │   ├── rest_path.py
│   │   └── service_name.py
│   ├── loaders/            ← Reads governance repo content
│   │   ├── base_loader.py  ← Abstract: read(), list(), validate(), get_config()
│   │   ├── local_loader.py ← Filesystem; validate() checks path exists
│   │   └── github_loader.py← GitHub API; validate() is no-op (errors surface on first call)
│   ├── models/
│   │   ├── config.py       ← GovernanceConfig, RuleConfig, RolloutConfig, per-rule configs
│   │   └── rollout.py      ← RolloutStatus (MCP response model)
│   ├── routes/
│   │   ├── validate.py     ← REST handlers: POST /validate/<resource-type>
│   │   └── incident.py     ← POST /webhook/incident (Incident-to-Eval Synthesis)
│   └── server.py           ← FastAPI app, MCP registration, _config() + _resolve_team()
├── tests/                  ← pytest unit tests (98 tests)
└── features/               ← Gherkin integration tests (behave, @enforced / @wip)
```

---

## Patterns in use

### Schema Validation Retry
After a failed `validate_*` call, the agent revises using the error messages as context and validates again. Max 2 attempts. Validators return structured errors specific enough to guide a retry:

```python
ValidationResult(valid=False, errors=["expected 7 dot-separated segments, got 3"], warnings=[])
```

### Agent Circuit Breaker
The server fails **closed** by default. `NOMOS_ON_UNAVAILABLE` controls behaviour:

- `fail` (default) — raises `RuntimeError`. The agent cannot proceed. Safe for production.
- `warn` — logs a warning, returns an empty `GovernanceConfig()`. Advisory/dev mode.

Implemented via a `validate()` hook on `BaseLoader` called before `get_config()`. This intercepts the error before the silent `FileNotFoundError → GovernanceConfig()` fallback in `get_config()`.

```python
# server.py — _config()
loader.validate()        # raises if repo unreachable
return loader.get_config()
```

### MCP Pattern Injection
Governance context is injected at agent generation time, not at prompt authoring time. Tools are independently queryable — agents load only what they need (`get_knowledge("failures")` → `get_kafka_conventions()` → `validate_topic_name(...)`).

### Incident-to-Eval Synthesis ✓ implemented
`POST /webhook/incident` converts a production violation into a PR against the governance repo:

1. Receives violation payload (`resource_name`, `resource_type`, `rule_violated`, `bad_pattern`, `correct_pattern`)
2. Formats a `failures.md` entry (`format_entry()` — pure function, injectable date)
3. Opens a GitHub PR: get main SHA → fetch existing file → create branch `incident/{date}-{slug}` → PUT file → open PR

Requires `GITHUB_TOKEN` and `NOMOS_REPO_PATH`. Returns 503 if not configured (fail-closed).

### Canary Rollout ✓ implemented
Rules can be enforced for a pilot team before rolling out to everyone. Controlled by a `rollout:` block in `governance.yml`:

```yaml
kafka:
  topic:
    rollout:
      phase: canary
      teams: [payments, platform]
```

`apply_rollout(result, rollout, team)` in `src/validators/rollout.py` is a **pure function** called at the end of every validator. If phase is canary and team is not in the list, errors are downgraded to warnings (`valid: true`). This keeps all rollout logic in one place — validators don't branch on it.

```python
# Every validator ends with:
return apply_rollout(ValidationResult(...), config.rollout, team)
```

---

## Coupling analysis

### What is fully decoupled — zero code changes needed

**Governance content** (constitutions, ADRs, knowledge, Gherkin features): the loaders read by generic path. Adding `knowledge/ml-patterns.md` or a new `constitutions/ml.md` requires no server changes.

**Rollout resolution**: `rollout_tools._resolve()` uses dotted attribute traversal over `GovernanceConfig`. Any config section that inherits `RuleConfig` is automatically reachable by its dotted path (`kafka.topic`, `kafka.service_account`, etc.). Adding a new `RuleConfig` subclass and wiring it into `GovernanceConfig` is sufficient — no changes to `rollout_tools.py`.

```python
# _resolve("kafka.topic", config) works for any RuleConfig attribute, present or future
obj = config
for part in rule_name.split("."):
    obj = getattr(obj, part, _SENTINEL)
rollout = getattr(obj, "rollout", _SENTINEL)
```

**Rule values**: anything configurable via `governance.yml` (prefixes, valid roles, SA envs, schema formats) changes without touching code.

### What requires code changes — adding a new resource type

Adding a new resource type (e.g. `ml-model`) requires touching **5 files**, always the same ones:

| File | What to add |
|---|---|
| `src/models/config.py` | `class MLModelConfig(RuleConfig): ...` + field in `GovernanceConfig` |
| `src/validators/ml_model.py` | `validate_ml_model(name, config, *, team=None) -> ValidationResult` + `apply_rollout()` at the end |
| `src/server.py` | `@mcp.tool()` decorator + `async def validate_ml_model(...)` |
| `src/routes/validate.py` | `Route("/validate/ml-model", endpoint=validate_ml_model_handler, methods=["POST"])` + handler |
| `src/__main__.py` | `elif command == "ml-model":` branch in both `_local()` and `_remote()` |

Each of these is an **explicit registration point** — MCP tools, REST routes, and CLI commands are all hardcoded. There is no auto-discovery registry.

### Why this coupling is acceptable

The explicit registration at 5 fixed points has concrete advantages:

1. **Greppability**: `git grep validate_ml_model` finds every integration point in one pass. There is no magic — the tool registration, the HTTP route, and the CLI branch are all visible in the source.

2. **Independent evolvability**: MCP, REST, and CLI surfaces can diverge. A tool can accept richer input than the REST body, or the CLI can add convenience flags that don't exist on the REST API. An automatic registry would force all three to share the same interface.

3. **Controlled blast radius**: A bug in a new validator doesn't affect existing validators. The explicit wiring makes it impossible for a new resource type to accidentally shadow an existing one.

4. **Low frequency**: new resource types are rare (the platform has had 6 for months). The cost of 5 file edits once every few months does not justify the complexity of an auto-discovery registry.

5. **Tests are explicit too**: each new validator has its own test file, each REST handler has its own test cases. The pattern is learnable and consistent.

The tradeoff would shift if the platform grew to 20+ resource types with frequent additions. At that point a registry pattern (`@validator(name="ml-model", path="/validate/ml-model", cli="ml-model")`) would pay off.

---

## Conventions

- All MCP tools return structured dicts, never plain strings
- Validator functions: `validate_<resource>(input, config: <ResourceConfig>, *, team: str | None = None) -> ValidationResult`
- Every validator calls `apply_rollout(result, config.rollout, team)` as its final return
- New tools: add to `src/tools/` if standalone logic, or directly in `server.py` as `@mcp.tool()` for simple wrappers; document in README.md
- Env vars use `NOMOS_` prefix
- REST endpoints: `POST /validate/<resource-type>` with JSON body `{"name": "...", "team": "..."}`
- Tests in `tests/` (pytest), Gherkin integration tests in `features/`
- `src/validators/rollout.py` and `src/tools/rollout_tools.py` — do not duplicate rollout logic; all rollout behaviour lives here

## Running locally

```bash
cd mcp-server
uv run python -m src --repo ../examples/kafka
# → http://127.0.0.1:8080

uv run pytest tests/ -q
GOVERNANCE_REPO_PATH=../examples/kafka uv run behave --tags=enforced
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `GOVERNANCE_REPO_PATH` | — | Path to governance repo (local mode) |
| `GOVERNANCE_REPO_URL` | — | GitHub URL (GitHub mode) |
| `GITHUB_TOKEN` | — | Required for GitHub mode and `/webhook/incident` |
| `NOMOS_ON_UNAVAILABLE` | `fail` | `fail` = error if repo unreachable; `warn` = empty config |
| `NOMOS_REPO_PATH` | — | `{owner}/{repo}` for incident PRs; falls back to `GOVERNANCE_REPO_URL` |

## Related repos

- [nomos-template](../nomos-template) — governance content this server reads
- [constitutional-governance](../constitutional-governance) — methodology docs and principles
