Feature: Kafka topic naming convention
  Reference: ADR-001
  Status: enforced

  All topics follow a seven-segment dot-separated scheme:
    {prefix}.{domain}.{group}.{project}.{component}.{name}.{version}

  The prefix drives retention defaults and RBAC wildcard boundaries.
  The version suffix is mandatory — it enables parallel schema evolution
  without blocking consumers during migrations. Hyphens are banned because
  they break some Confluent tooling and make regex RBAC patterns ambiguous.

  @enforced
  Scenario: Complete valid topic name passes
    Given the topic name "raw.sales.pos.hmsu.commons.guestcheck.v1"
    When I validate it
    Then validation passes

  @enforced
  Scenario: kstreams internal topic passes
    Given the topic name "kstreams.sales.pos.hmsu.receipt.dlq.v1"
    When I validate it
    Then validation passes

  @enforced
  Scenario: landing topic for a connector source passes
    Given the topic name "landing.sales.pos.lsretail.lookup.product.v1"
    When I validate it
    Then validation passes

  @enforced
  Scenario: Fewer than seven segments is rejected
    Given the topic name "raw.sales.pos.hmsu.v1"
    When I validate it
    Then validation fails
    And the error contains "expected 7 dot-separated segments"

  @enforced
  Scenario: Unknown prefix is rejected
    Given the topic name "internal.sales.pos.hmsu.commons.guestcheck.v1"
    When I validate it
    Then validation fails
    And the error contains "invalid prefix"

  @enforced
  Scenario: Missing version suffix is rejected
    Given the topic name "raw.sales.pos.hmsu.commons.guestcheck.latest"
    When I validate it
    Then validation fails
    And the error contains "v[0-9]+"

  @enforced
  Scenario: Uppercase letters anywhere in the name are rejected
    Given the topic name "raw.Sales.pos.hmsu.commons.guestcheck.v1"
    When I validate it
    Then validation fails
    And the error contains "lowercase"

  @enforced
  Scenario: Hyphens inside a segment are rejected
    Given the topic name "raw.sales.pos.hmsu.commons.guest-check.v1"
    When I validate it
    Then validation fails
    And the error contains "hyphen"

  @enforced
  Scenario: dev prefix passes but warns about production use
    Given the topic name "dev.sales.pos.hmsu.commons.guestcheck.v1"
    When I validate it
    Then validation passes
    And a warning is raised about "dev"
