Feature: Helm resource limits and requests
  Reference: ADR-006
  Status: wip — validator pending

  All services must declare memory requests and limits. CPU limits are
  intentionally omitted platform-wide to avoid CPU throttling under burst
  load — the scheduler uses requests for placement only. Memory limits
  are enforced to prevent OOMKilled cascades across the node.

  @wip
  Scenario: values.yml declares memory request
    Given a service values.yml
    When I check resources.requests.memory
    Then the value is set and not empty

  @wip
  Scenario: values.yml declares memory limit
    Given a service values.yml
    When I check resources.limits.memory
    Then the value is set and not empty

  @wip
  Scenario: CPU limits are not set
    Given a service values.yml
    When I check resources.limits.cpu
    Then the value is absent or commented out
