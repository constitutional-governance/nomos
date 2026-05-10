"""
nomos scaffold — generate scaffolding files for a new governance domain.

Creates:
  constitutions/<name>.md          — domain constitution template
  adrs/<name>/001-resource-naming.md  — first ADR template
  features/<name>/<name>-conventions.feature  — Gherkin check template (@wip)

Usage:
    nomos scaffold domain kafka
    nomos scaffold domain rest-api --repo /path/to/governance-repo
"""
import os
from datetime import date
from pathlib import Path


_CONSTITUTION = """\
# {title} Constitution

**Domain:** `{name}`
**Owner:** TODO — assign a domain owner in GOVERNANCE-PROCESS.md

---

## Purpose

TODO — describe what this domain governs and why these rules exist.

---

## Non-negotiable invariants

These rules apply to every {title} resource, regardless of team:

1. TODO — first invariant
2. TODO — second invariant

---

## Naming conventions

TODO — describe the naming patterns for resources in this domain.
Reference: [ADR-001](../adrs/{name}/001-resource-naming.md)

---

## Scope

**What belongs here:** TODO

**What does not belong here:** TODO
"""

_ADR = """\
# ADR-001: {title} Resource Naming Convention

**Status:** Proposed
**Date:** {today}
**Domain:** `{name}`

## Decision

TODO — describe the naming convention you are adopting.

## Rationale

TODO — why does this convention exist? What problem does it solve?

## Alternatives rejected

TODO — what else did you consider and why did you reject it?

## Consequences

**Easier:** TODO

**Harder:** TODO
"""

_FEATURE = """\
@wip
Feature: {title} naming convention

  Background:
    Given the {name} governance rules are loaded

  @wip
  Scenario: valid resource name is accepted
    Given the {name} resource name "TODO-insert-valid-example"
    When I validate the {name} resource name
    Then it should be valid

  @wip
  Scenario: invalid resource name is rejected
    Given the {name} resource name "TODO-insert-invalid-example"
    When I validate the {name} resource name
    Then it should be invalid
    And the error should mention "TODO-what-rule-it-violates"
"""

_GOVERNANCE_YML_HINT = """\
# ── governance.yml addition ───────────────────────────────────────────────────
# Add this section to governance.yml to enable validation for the {name} domain:
#
# {name}:
#   # TODO — add validation rules
#   # See examples/kafka/governance.yml for reference
# ─────────────────────────────────────────────────────────────────────────────
"""


def run(args) -> int:
    name = args.name.lower().replace(" ", "-")
    title = name.replace("-", " ").title()
    repo_path = Path(
        args.repo if args.repo else os.environ.get("GOVERNANCE_REPO_PATH", ".")
    ).resolve()
    today = date.today().isoformat()

    ctx = {"name": name, "title": title, "today": today}

    files = [
        (repo_path / "constitutions" / f"{name}.md", _CONSTITUTION.format(**ctx)),
        (repo_path / "adrs" / name / "001-resource-naming.md", _ADR.format(**ctx)),
        (repo_path / "features" / name / f"{name}-conventions.feature", _FEATURE.format(**ctx)),
    ]

    any_created = False
    for path, content in files:
        if path.exists():
            print(f"SKIP {path.relative_to(repo_path)} already exists")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"OK   {path.relative_to(repo_path)}")
            any_created = True

    if not any_created:
        print()
        print("Nothing created — all files already exist.")
        return 0

    print()
    print(_GOVERNANCE_YML_HINT.format(**ctx))
    print("Next steps:")
    print(f"  1. Edit constitutions/{name}.md — define invariants and naming rules")
    print(f"  2. Edit adrs/{name}/001-resource-naming.md — record the naming decision")
    print(f"  3. Edit features/{name}/{name}-conventions.feature — write Gherkin checks")
    print(f"  4. Add `{name}:` section to governance.yml")
    print(f"  5. Add {title} to the domain ownership table in GOVERNANCE-PROCESS.md")
    print(f"  6. Promote @wip → @enforced: nomos check-promotion features/{name}/{name}-conventions.feature --run")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "scaffold",
        help="Generate scaffolding files for a new governance domain",
    )
    p.add_argument(
        "type",
        choices=["domain"],
        metavar="TYPE",
        help="Artifact type to scaffold. Currently supported: domain",
    )
    p.add_argument(
        "name",
        help="Domain name (e.g. kafka, camel, rest-api)",
    )
    p.add_argument(
        "--repo",
        metavar="PATH",
        help="Governance repo path (default: GOVERNANCE_REPO_PATH env var, or .)",
    )
    p.set_defaults(func=run)
