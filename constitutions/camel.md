# Camel Constitution

> Replace with your organization's Apache Camel-specific principles.

## Route naming

All Camel route IDs follow a camelCase verb-noun pattern. Route IDs are defined as constants — no magic strings in route definitions.

## Application naming

Camel application names follow the pattern `kafka-camel-{repo-name}` and are set in `camel.main.name` in `application-docker.yml`.

## Consumer groups

Camel integrations use the `kafka.camel.*` consumer group prefix, aligned with the application name and route direction.

## Error handling

Every route declares explicit error handling. The default error handler is prohibited in production — use a dead letter channel pointing to a `.dlq.v1` topic.

## Base class

All routes extend the organization's base route builder class (configured in `governance.yml` under `camel.base_class`).
