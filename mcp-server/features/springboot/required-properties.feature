Feature: SpringBoot required application properties
  Reference: ADR-005
  Status: wip — validator pending

  application-docker.yml is the profile used in all containerised
  environments. It must configure Kafka connectivity, Schema Registry,
  and the Spring application name. Missing or hardcoded values cause
  silent failures that only surface at runtime.

  @wip
  Scenario: spring.application.name is set
    Given a SpringBoot application-docker.yml
    When I check spring.application.name
    Then the property is set and not empty

  @wip
  Scenario: bootstrap-servers references an environment variable
    Given a SpringBoot application-docker.yml
    When I check spring.kafka.bootstrap-servers
    Then the value uses ${...} placeholder syntax, not a hardcoded host

  @wip
  Scenario: Schema Registry URL references an environment variable
    Given a SpringBoot application-docker.yml with Schema Registry configured
    When I check spring.kafka.properties.schema.registry.url
    Then the value uses ${...} placeholder syntax

  @wip
  Scenario: SASL credentials reference environment variables
    Given a SpringBoot application-docker.yml
    When I check spring.kafka.properties.sasl.jaas.config
    Then both username and password use ${...} placeholder syntax

  @wip
  Scenario: Truststore location points to the CSI mount path
    Given a SpringBoot application-docker.yml
    When I check spring.kafka.properties.ssl.truststore.location
    Then the value starts with "/mnt/secrets/"
