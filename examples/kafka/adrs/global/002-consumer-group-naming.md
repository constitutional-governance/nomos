---
id: "002"
title: "Consumer Group Naming"
status: "Accepted"
domain: "kafka"
version: 1
date: "2025-01-01"
---

# ADR-002: Consumer Group Naming

## Status

Accepted

## Context

Consumer group IDs determine offset tracking and partition assignment. Auto-generated IDs make it impossible to trace a consumer group back to the application that owns it. Consistent consumer group naming enables observability, RBAC scoping, and lag alerting.

## Decision

Consumer group IDs follow different patterns depending on the framework:

### KStreams

```
kstreams.{domain}.{group}.{project}.{app-name}
```

Example: `kstreams.retail.pos.acme.receipt-processor`

The `kstreams.*` prefix is used for all KStreams applications including internal changelog and repartition topics.

### Apache Camel

```
kafka.camel.{domain}.{group}.{project}.{component}.{direction}.{version}
```

Example: `kafka.camel.retail.pos.acme.receipt.src.v1`

The `kafka.camel.*` prefix is used for all Camel integrations.

## Rules

- Consumer group IDs must be set explicitly — never rely on framework-generated defaults
- The RBAC pattern for granting `DeveloperRead` on consumer groups uses the same prefix: `kstreams.{domain}.*` or `kafka.camel.{domain}.*`

## Consequences

- Every consumer group is traceable to its owning application
- RBAC wildcards can be scoped to a domain without over-permissioning
- Lag alerts can be attributed to specific applications
