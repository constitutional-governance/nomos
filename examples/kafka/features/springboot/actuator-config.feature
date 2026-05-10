Feature: SpringBoot actuator endpoint configuration
  Reference: ADR-005
  Status: wip — validator pending

  The actuator must not expose sensitive endpoints (env, beans, heapdump)
  in non-dev environments. Management port should be separate from the
  application port to allow network policies to restrict actuator access
  to cluster-internal traffic only.

  @wip
  Scenario: Actuator does not expose env endpoint in docker profile
    Given a SpringBoot application-docker.yml
    When I check management.endpoints.web.exposure.include
    Then "env" is not in the exposed endpoints list

  @wip
  Scenario: Actuator does not expose heapdump endpoint in docker profile
    Given a SpringBoot application-docker.yml
    When I check management.endpoints.web.exposure.include
    Then "heapdump" is not in the exposed endpoints list

  @wip
  Scenario: Management port is configured
    Given a SpringBoot application-docker.yml
    When I check management.server.port
    Then the port is set (default 8080 is acceptable if not separately configured)
