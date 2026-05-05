---
id: "007"
title: "Schema Registry Conventions"
status: "Accepted"
domain: "kafka"
version: 1
date: "2025-01-01"
---

# ADR-007: Schema Registry Conventions

## Status

Accepted

## Context

Schema Registry subjects must be predictable and traceable to the topic they belong to. AVRO namespaces must be globally unique and reflect the domain hierarchy to avoid collisions as the schema catalogue grows.

## Decision

### Subject naming

The default TopicNameStrategy applies:

```
{topic-name}-value
{topic-name}-key   (only when the key carries structured data)
```

Example:
```
raw.retail.pos.acme.orders.receipt.v1-value
```

### AVRO namespace

```
com.{org}.kafka.{domain}.{group}.{project}.{component}
```

Example: `com.example.kafka.retail.pos.acme.orders`

Replace `{org}` with your organization's reverse-DNS prefix.

### Compatibility

Default compatibility level: **BACKWARD**

Exceptions require a new topic version (v2, v3, …) rather than a compatibility downgrade.

### Schema versioning

Schema version is encoded in the topic name, not in the subject. Subject `raw.retail.pos.acme.orders.receipt.v1-value` tracks evolution of the v1 schema. A breaking change produces `raw.retail.pos.acme.orders.receipt.v2-value` as a new subject.

## Consequences

- Subjects are 1:1 with topics — no ambiguity about which schema applies
- AVRO namespaces are globally unique and domain-traceable
- Breaking changes require a new topic version — old consumers continue working on v1 until migrated
