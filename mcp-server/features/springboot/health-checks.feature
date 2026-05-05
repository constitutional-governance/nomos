Feature: SpringBoot health check configuration
  Reference: ADR-005
  Status: wip — validator pending

  Kubernetes liveness and readiness probes are configured in the Helm
  values.yml and point to actuator endpoints. If the actuator health groups
  are not enabled in application.yml, the probe path returns 404 and
  Kubernetes kills the pod immediately after startup.

  KStreams services expose a 'kstreams' health group at
  /actuator/health/kstreams — used by the liveness probe. Camel services
  use /actuator/health/liveness and /actuator/health/readiness with a
  dedicated startupProbe at /actuator/health/startup.

  @wip
  Scenario: Liveness state is enabled
    Given a SpringBoot application.yml
    When I check management.health.livenessstate.enabled
    Then the value is "true"

  @wip
  Scenario: Readiness state is enabled
    Given a SpringBoot application.yml
    When I check management.health.readinessstate.enabled
    Then the value is "true"

  @wip
  Scenario: KStreams service enables the kstreams health group
    Given a KStreams SpringBoot application.yml
    When I check management.endpoint.health.group.kstreams
    Then the group is defined and includes the kstreams indicator

  @wip
  Scenario: Actuator info and health endpoints are exposed
    Given a SpringBoot application.yml
    When I check management.endpoints.web.exposure.include
    Then it includes at least "health" and "info"

  @wip
  Scenario: show-details is not set to always in non-dev environments
    Given a SpringBoot application-docker.yml (qa or prod profile)
    When I check management.endpoint.health.show-details
    Then the value is not "always"
