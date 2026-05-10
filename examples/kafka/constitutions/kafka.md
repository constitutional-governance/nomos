# Kafka Constitution

> Replace with your organization's Kafka-specific principles.

## Topics

- Every topic name encodes prefix, domain, group, project, component, name, and version
- Topic names are immutable — rename = new topic + migration
- All topics require a registered AVRO schema before going to production

## Consumer groups

- KStreams applications use the `kstreams.*` prefix
- Camel integrations use the `kafka.camel.*` prefix
- Consumer group IDs must be set explicitly — never rely on auto-generated IDs

## RBAC

- `DeveloperRead` for consumers, `DeveloperWrite` for producers
- `DeveloperManage` is only valid on `resource_type = cluster`
- Service accounts are scoped to a single system

## Schema Registry

- Default compatibility: BACKWARD
- Namespace: `com.{org}.kafka.{domain}.{group}.{project}.{component}`
- No schema deletion in production

## KStreams

- Every state store has a named state store ending in `.store`
- Every `Named.as()` call uses the pattern `{service}.{operation}.{entity}.{seq}`
- Internal changelog and repartition topics use the `kstreams.*` prefix
