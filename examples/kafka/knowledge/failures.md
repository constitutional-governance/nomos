# AI Failure Patterns — Kafka Platform

Systematic patterns where AI-generated resources violated governance rules.
Review these before generating any Kafka resource.

---

## Topic naming: wrong segment count

- **Resource**: `raw.payments.pos.checkout.v1`
- **Bad pattern**: 5 segments — missing domain and team
- **Correct pattern**: `raw.payments.pos.acme.checkout.receipt.v1` (7 segments: env.domain.subdomain.team.entity.event.version)
- **Rule violated**: `kafka.topic` — `segment_count = 7`
- **Reported**: 2026-03-12

---

## Topic naming: invalid environment prefix

- **Resource**: `test.payments.pos.acme.checkout.receipt.v1`
- **Bad pattern**: `test` prefix — not in the declared prefix list
- **Correct pattern**: `dev.payments.pos.acme.checkout.receipt.v1` or `raw.payments.pos.acme.checkout.receipt.v1`
- **Rule violated**: `kafka.topic` — `prefixes = [raw, public, ready, private, dev]`
- **Reported**: 2026-03-18

---

## Topic naming: uppercase characters

- **Resource**: `raw.Payments.POS.acme.Checkout.Receipt.v1`
- **Bad pattern**: mixed case — Kafka topic names must be fully lowercase
- **Correct pattern**: `raw.payments.pos.acme.checkout.receipt.v1`
- **Rule violated**: `kafka.topic` — segment pattern requires lowercase alphanumeric and hyphens only
- **Reported**: 2026-04-02

---

## Service account naming: missing connector direction

- **Resource**: `sa-payments-connector-jdbc-prod`
- **Bad pattern**: `connector` SA without `source` or `sink` direction segment
- **Correct pattern**: `sa-payments-connector-source-jdbc-prod`
- **Rule violated**: `kafka.service_account` — connector SAs require `source` or `sink` after `connector`
- **Reported**: 2026-03-25

---

## Service account naming: wrong prefix

- **Resource**: `svc-payments-producer-prod`
- **Bad pattern**: `svc-` prefix instead of `sa-`
- **Correct pattern**: `sa-payments-producer-prod`
- **Rule violated**: `kafka.service_account` — `prefix = "sa-"`
- **Reported**: 2026-04-10

---

## RBAC: invalid role name

- **Resource**: `developer.payments / Topic / raw.payments.*`
- **Bad pattern**: lowercase role name `developer.payments` — not in the valid roles list
- **Correct pattern**: `DeveloperRead` for read-only topic access
- **Rule violated**: `kafka.rbac` — `valid_roles` must be one of the declared roles
- **Reported**: 2026-04-15

---

## RBAC: cluster-scoped role on topic resource

- **Resource**: `DeveloperManage / Topic / raw.payments.pos.acme.checkout.receipt.v1`
- **Bad pattern**: admin role `DeveloperManage` applied to a topic — admin roles are reserved for cluster-level resources
- **Correct pattern**: `DeveloperManage / Cluster / kafka-cluster` or use `DeveloperRead` / `DeveloperWrite` on the topic
- **Rule violated**: `kafka.rbac` — `admin_roles` may only bind to `admin_resource_types`
- **Reported**: 2026-04-22

---

## Schema: unsupported compatibility level

- **Resource**: `AVRO / BREAKING`
- **Bad pattern**: `BREAKING` is not a valid compatibility level
- **Correct pattern**: `AVRO / BACKWARD` (default) — use `FORWARD` or `FULL` for stricter guarantees
- **Rule violated**: `kafka.schema_registry` — `valid_compatibility_levels`
- **Reported**: 2026-05-05

---

## REST path: missing API version

- **Resource**: `/payments/orders/{orderId}/items`
- **Bad pattern**: no version prefix — breaks client contract management
- **Correct pattern**: `/v1/payments/orders/{orderId}/items`
- **Rule violated**: `rest_api` — `require_version = true`, `versioning_strategy = path`
- **Reported**: 2026-05-08

---

## Service name: exceeds max length

- **Resource**: `payments-pos-acme-checkout-receipt-processor-service`
- **Bad pattern**: 51 characters — exceeds Kubernetes DNS label limit
- **Correct pattern**: `payments-checkout-receipt-processor` (≤ 63 characters, descriptive but concise)
- **Rule violated**: `service` — `max_length = 63`, pattern `^[a-z][a-z0-9-]{1,61}[a-z0-9]$`
- **Reported**: 2026-05-14
