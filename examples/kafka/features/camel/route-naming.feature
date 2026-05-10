Feature: Apache Camel route naming convention
  Reference: ADR-004
  Status: wip — validator pending

  Camel route IDs are the source of consumer group names. A route without
  an explicit ID generates a consumer group based on the Java class name,
  which breaks the kafka.camel.* RBAC wildcard and makes offset tracking
  impossible to attribute to a specific route during incidents.

  Route IDs are declared as constants in Constants.java and passed to
  .routeId(Constants.ROUTE_ID_XYZ). This makes them refactor-safe and
  grep-able across the repo.

  @wip
  Scenario: Every Camel route declares an explicit route ID
    Given a Camel route builder class
    When I scan for .from() calls
    Then every from() chain has a .routeId() call before any processor

  @wip
  Scenario: Route IDs are defined as constants, not inline strings
    Given a Camel route builder class
    When I check routeId() arguments
    Then each argument references a constant from Constants.java, not a literal string

  @wip
  Scenario: Camel application name follows the repo naming pattern
    Given the camel.main.name property in application.yml
    When I check its value
    Then it matches "kafka-camel-{repo-name}"

  @wip
  Scenario: Camel Kafka consumer sets groupId explicitly
    Given a Camel Kafka consumer endpoint URI
    When I check the groupId parameter
    Then it is set explicitly and starts with "kafka.camel."

  @wip
  Scenario: Route extends BaseRouteBuilder from the platform starter
    Given a Camel route builder class
    When I check the class declaration
    Then it extends BaseRouteBuilder, not RouteBuilder directly
