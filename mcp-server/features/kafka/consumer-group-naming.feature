Feature: Kafka consumer group naming convention
  Reference: ADR-002
  Status: wip — validator pending

  Consumer group IDs drive RBAC wildcard bindings. If a service uses a
  framework-generated ID (e.g. the Spring application name), the wildcard
  ResourceOwner binding on kstreams.{domain}.* breaks — the group falls
  outside the declared pattern and the service loses ownership of its offsets.

  KStreams apps must use kstreams.* prefix. Camel integrations must use
  kafka.camel.* prefix. Both must be set explicitly in configuration,
  never left to framework defaults.

  @wip
  Scenario: KStreams app sets consumer group explicitly with kstreams prefix
    Given a KStreams application with spring.kafka.streams.application-id configured
    When I check the value
    Then it starts with "kstreams."
    And it matches the pattern "kstreams.{domain}.{group}.{project}.{app-name}.{version}"

  @wip
  Scenario: Camel integration sets consumer group explicitly with kafka.camel prefix
    Given a Camel route with camel.component.kafka.group-id configured
    When I check the value
    Then it starts with "kafka.camel."

  @wip
  Scenario: Consumer group is not a Java class name or Spring application name
    Given a consumer group ID
    When I check the value
    Then it does not match a fully qualified Java class name pattern
    And it does not equal the spring.application.name value

  @wip
  Scenario: Identity pool RBAC grants ResourceOwner on kstreams groups for the domain
    Given a domain rbac.hcl with a KStreams identity pool
    When I check the role bindings for group resources
    Then it declares ResourceOwner on "kstreams.{domain}.*" group resources

  @wip
  Scenario: Identity pool RBAC grants ResourceOwner on kafka.camel groups for the domain
    Given a domain rbac.hcl with a Camel identity pool
    When I check the role bindings for group resources
    Then it declares ResourceOwner on "kafka.camel.{domain}.*" group resources
