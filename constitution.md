# Platform Constitution

> Replace this file with your organization's platform-wide principles.
> Keep it under 150 lines — this is a pointer document, not a reference manual.

## Core principles

1. **Explicit over implicit** — Name every resource to express intent. Consumers must understand what a topic, service account, or consumer group does without reading the code.

2. **Schema first** — No producer ships without a registered schema. Breaking schema changes require a new topic version.

3. **Governance as code** — Naming rules, RBAC constraints, and architectural decisions live in this repo. ADRs are the audit trail for every platform decision.

4. **Separation of concerns** — Platform infrastructure (clusters, networking) is managed separately from domain resources (topics, schemas, service accounts). See `adrs/global/` for the full rationale.

5. **AI-assisted, human-approved** — Agents use this governance server to propose correct names and configurations. A human reviews and approves every change.

## Domain constitutions

| Domain | File |
|---|---|
| Global | this file |
| Kafka | `constitutions/kafka.md` |
| Camel | `constitutions/camel.md` |

## ADR index

See `adrs/global/` for all Architecture Decision Records.
