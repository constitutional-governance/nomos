# govern-mcp server

MCP server for the govern-mcp governance engine. Exposes ADRs, constitutions, naming conventions, Gherkin checks, and real-time validators as MCP tools.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # edit GOVERNANCE_REPO_PATH to point at the repo root
.venv/bin/python -m src.main  # starts on http://127.0.0.1:8080
```

Or use the root `setup.sh` — it does all of the above.

## Configuration

The server reads two things at startup:

- **`.env`** — runtime settings (server port, governance mode, GitHub token, cache TTL)
- **`governance.yml`** at the governance repo root — your org's naming rules (read via `GOVERNANCE_REPO_PATH`)

In GitHub mode (`GOVERNANCE_MODE=github`), the server fetches files from the GitHub API and caches them for `CACHE_TTL_SECONDS`. A webhook to `POST /webhook/github` invalidates the cache.

## Tests

```bash
# Unit tests
.venv/bin/pytest tests/ -q

# Behave (Gherkin executable checks, enforced only)
.venv/bin/behave --tags=enforced

# Everything including @wip scenarios
.venv/bin/behave --no-skipped
```

## CLI validator

```bash
.venv/bin/governance-validate topic raw.sales.pos.hmsu.commons.guestcheck.v1
.venv/bin/governance-validate rbac DeveloperRead topic "raw.sales.*"
.venv/bin/governance-validate sa sa-sales-lsretail-lookup-connector-source-jdbc-dev
```

Exit 0 = valid, 1 = errors. Use as a pre-commit hook or in CI.

## Directory structure

```
src/
├── server.py          # MCP tool definitions (FastMCP)
├── __main__.py        # CLI entry point
├── config.py          # Pydantic settings (.env)
├── validators/        # topic.py, rbac.py, sa_naming.py
├── loaders/           # local_loader.py, github_loader.py, base_loader.py
├── models/            # config.py (GovernanceConfig), validation.py, adr.py, …
└── tools/             # adr_tools.py, constitution_tools.py, check_tools.py, …

features/
├── environment.py     # Behave before_all — loads GovernanceConfig into context
├── kafka/             # topic-naming, rbac-bindings, sa-naming, consumer-group-naming
├── camel/             # error-handler-config (@wip)
├── helm/              # resource-standards (@wip)
└── springboot/        # required-properties (@wip)
```

## Adding a new validator

1. Add rules to `governance.yml` and update the Pydantic model in `src/models/config.py`
2. Write the validator in `src/validators/`
3. Expose it as an MCP tool in `src/server.py` and a CLI command in `src/__main__.py`
4. Add Gherkin scenarios in `features/<domain>/` with `@enforced` tag
5. Add step definitions in `features/steps/validation_steps.py`
