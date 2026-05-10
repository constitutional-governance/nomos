Feature: Service account naming convention
  Reference: ADR-002
  Status: enforced

  Service account keys in rbac.hcl are used directly as display_name in
  Confluent Cloud. A consistent naming scheme makes it possible to identify
  the owning domain, the connector type, and the environment from the name
  alone — without querying the Confluent API.

  Patterns:
    Standard:   sa-{domain}-{system}-...-{env}
    Connector:  sa-{domain}-{system}-connector-{source|sink}-{type}-{env}
    Debug:      sa-{domain}-{system}-{env}-debug

  env must be one of: dev, qa, prod

  @enforced
  Scenario: Valid JDBC source connector SA passes
    Given a service account named "sa-sales-lsretail-lookup-connector-source-jdbc-dev"
    When I validate it
    Then validation passes

  @enforced
  Scenario: Valid sink connector SA passes
    Given a service account named "sa-sales-pos-hmsu-connector-sink-jdbc-prod"
    When I validate it
    Then validation passes

  @enforced
  Scenario: Valid debug SA passes
    Given a service account named "sa-sales-hmsu-dev-debug"
    When I validate it
    Then validation passes

  @enforced
  Scenario: Valid standard SA passes
    Given a service account named "sa-sales-pos-hmsu-dev"
    When I validate it
    Then validation passes

  @enforced
  Scenario: Missing sa- prefix is rejected
    Given a service account named "sales-lsretail-lookup-dev"
    When I validate it
    Then validation fails
    And the error contains "sa-"

  @enforced
  Scenario: Invalid environment suffix is rejected
    Given a service account named "sa-sales-lsretail-lookup-connector-source-jdbc-staging"
    When I validate it
    Then validation fails
    And the error contains "environment"

  @enforced
  Scenario: Unknown connector direction is rejected
    Given a service account named "sa-sales-lsretail-lookup-connector-push-jdbc-dev"
    When I validate it
    Then validation fails
    And the error contains "source"

  @enforced
  Scenario: Uppercase letters are rejected
    Given a service account named "sa-Sales-lsretail-dev"
    When I validate it
    Then validation fails
    And the error contains "lowercase"
