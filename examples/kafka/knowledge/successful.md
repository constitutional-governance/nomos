# Successful Patterns — Kafka Platform

Approaches and patterns that have worked well. Use these as reference when generating resources.

---

## Topic naming: full 7-segment hierarchy

The full `env.domain.subdomain.team.entity.event.version` hierarchy makes topics self-documenting.
CI topic validation catches violations before they reach the broker.

```
raw.payments.pos.acme.checkout.receipt.v1
│   │        │   │    │        │       └─ version
│   │        │   │    │        └───────── event (what happened)
│   │        │   │    └────────────────── entity (what it happened to)
│   │        │   └─────────────────────── team
│   │        └─────────────────────────── subdomain
│   └──────────────────────────────────── domain
└──────────────────────────────────────── environment prefix
```

**Validated example**:

```
raw.payments.pos.acme.checkout.receipt.v1   ✓ valid — 7 segments, known prefix, lowercase
dev.logistics.wms.globus.shipment.created.v2 ✓ valid — dev environment, non-production prefix
```

---

## Service account naming: role-based + env suffix

Embedding the SA role (producer/consumer/connector) and environment as the last segment makes
RBAC audits fast: the SA name alone reveals what it does and where it runs.

```
sa-{team}-{role}-{env}
sa-{team}-connector-{direction}-{connector-type}-{env}
```

**Validated examples**:

```
sa-payments-producer-prod              ✓ producer SA for payments team in production
sa-payments-consumer-prod              ✓ consumer SA for payments team in production
sa-payments-connector-source-jdbc-prod ✓ JDBC source connector for payments in production
sa-logistics-connector-sink-s3-dev     ✓ S3 sink connector for logistics in development
```

---

## RBAC: minimal privilege bindings

Bind the least-privileged role that satisfies the use case. `DeveloperRead` for consumers,
`DeveloperWrite` for producers, `DeveloperManage` only for the cluster resource itself.

```yaml
# Producer binding
role_name: DeveloperWrite
resource_type: Topic
resource_name: raw.payments.pos.acme.checkout.receipt.v1

# Consumer binding
role_name: DeveloperRead
resource_type: Topic
resource_name: raw.payments.pos.acme.*

# Cluster admin (ops only)
role_name: DeveloperManage
resource_type: Cluster
resource_name: kafka-cluster
```

---

## Schema registry: BACKWARD compatibility by default

Starting every schema with `BACKWARD` compatibility allows consumers to upgrade before producers.
Move to `FULL` for schemas shared across many independent teams.

```
AVRO / BACKWARD            ✓ safe default — consumers can roll forward
AVRO / FULL_TRANSITIVE     ✓ strict — use when schema is a public contract
PROTOBUF / BACKWARD        ✓ protobuf with backward compat
```

---

## REST API: versioned resource paths

All endpoints start with `/v{N}/` and use kebab-case. Path parameters use `{camelCase}`.
This keeps URLs consistent and avoids breaking changes when resource models evolve.

```
/v1/payments/orders/{orderId}/items       ✓ versioned, kebab-case, camelCase param
/v1/logistics/shipments/{shipmentId}      ✓ versioned, plural noun
/v2/platform/connectors/{connectorId}/status ✓ status as sub-resource, not query param
```

---

## Canary rollout: validate new rules against one team first

When introducing a new governance rule, set `phase: canary` and list one team.
Non-canary teams receive warnings instead of errors — they can still ship.
Promote to `phase: stable` once the canary team has adapted.

```yaml
kafka:
  topic:
    rollout:
      phase: canary
      teams:
        - payments
```

Check rollout state: `nomos-validate --server https://governance.acme.com get_rollout_status kafka.topic`
