---
id: "001"
title: "Kafka Topic Naming"
status: "Accepted"
domain: "kafka"
version: 1
date: "2025-01-01"
---

# ADR-001: Kafka Topic Naming

## Status

Accepted

## Context

Topic names are permanent. Once a topic is created in production, renaming it requires a full migration. A consistent naming scheme makes ownership, data classification, and lifecycle immediately visible from the name alone.

## Decision

Every topic name must follow the pattern:

```
{prefix}.{domain}.{group}.{project}.{component}.{name}.{version}
```

- **prefix** — data classification (raw, public, ready, private, kstreams, kcamel, sink, landing, dev)
- **domain** — business domain (e.g. retail, finance, logistics)
- **group** — sub-domain or channel (e.g. pos, crm, erp)
- **project** — originating system or project
- **component** — bounded context or module
- **name** — event or entity name
- **version** — schema version (v1, v2, …)

Rules:
- Exactly 7 segments (configured in `governance.yml`)
- All lowercase, dot-separated
- No hyphens within a segment — use dots only
- Maximum 249 characters

## Examples

```
raw.retail.pos.acme.orders.receipt.v1
public.retail.pos.acme.orders.receipt.v2
kstreams.retail.pos.acme.receipt.dlq.v1
```

## Consequences

- Topic names encode enough context to understand ownership and classification without reading code
- The `dev` prefix warns agents when topics are created in a non-production prefix
- Renaming a topic in production requires a migration — a new topic with the correct name plus a Cluster Link mirror
