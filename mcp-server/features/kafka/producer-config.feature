Feature: Kafka producer and consumer configuration standards
  Reference: ADR-005
  Status: wip — validator pending

  The platform currently runs on Kafka2/CFK using SASL_PLAIN over SSL with
  a JKS truststore. OAUTHBEARER is the target state for Confluent Cloud but
  is not yet in use. All credentials must come from environment variables
  injected by the Helm chart via Azure Key Vault CSI driver — never hardcoded.

  Auto-commit is disabled platform-wide. Consumers own their offset commits
  explicitly to enable exactly-once processing guarantees via KStreams or
  manual commit in Camel.

  @wip
  Scenario: Kafka client uses SASL_SSL security protocol
    Given a Kafka client configuration (producer or consumer)
    When I check the security.protocol property
    Then it is "SASL_SSL"

  @wip
  Scenario: Kafka client uses PLAIN mechanism (current Kafka2 platform)
    Given a Kafka client configuration
    When I check the sasl.mechanism property
    Then it is "PLAIN"

  @wip
  Scenario: SASL credentials come from environment variables
    Given a Kafka client configuration
    When I check sasl.jaas.config
    Then the username and password reference environment variables, not literal values

  @wip
  Scenario: Truststore location comes from the CSI-mounted secret path
    Given a Kafka client configuration
    When I check ssl.truststore.location
    Then it starts with "/mnt/secrets/"

  @wip
  Scenario: Consumer disables auto-commit
    Given a Kafka consumer configuration
    When I check enable.auto.commit
    Then it is "false"

  @wip
  Scenario: Schema Registry URL is not hardcoded
    Given a Kafka client with Schema Registry
    When I check schema.registry.url
    Then it references an environment variable
