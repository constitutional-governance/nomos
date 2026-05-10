Feature: Helm values.yml required structure
  Reference: ADR-006
  Status: wip — validator pending

  All microservices use a shared library Helm chart. There is no per-service
  Chart.yaml — the chart is provided by the platform. Each service supplies
  a values.yml per environment under pipelines/cd/{env}/values.yml.

  The values.yml must declare envVariables, secrets (CSI Key Vault driver),
  and probe definitions. Missing keys cause silent deployment failures
  because the library chart templates render with empty values.

  @wip
  Scenario: values.yml declares envVariables section
    Given a service values.yml
    When I check for the envVariables key
    Then the key is present and is a list

  @wip
  Scenario: values.yml declares a kafka secret with CSI driver
    Given a service values.yml for a Kafka client
    When I check the secrets section
    Then there is a secret named "kafka" with a csi.objects list

  @wip
  Scenario: kafka secret includes the user password object
    Given a service values.yml
    When I check secrets[kafka].csi.objects
    Then there is an entry with objectAlias "kafka-user.password"

  @wip
  Scenario: kafka secret includes the truststore JKS object
    Given a service values.yml
    When I check secrets[kafka].csi.objects
    Then there is an entry with objectAlias "truststore.jks" and objectEncoding "base64"

  @wip
  Scenario: KStreams processor declares a persistent volume for state store
    Given a KStreams service values.yml
    When I check the volumes section
    Then there is a volume with storageClassName "kafka-standardssd-retain"

  @wip
  Scenario: liveness probe path matches the service type
    Given a KStreams service values.yml
    When I check livenessProbe.httpGet.path
    Then the path is "/actuator/health/kstreams"

  @wip
  Scenario: Camel integration declares a startupProbe
    Given a Camel service values.yml
    When I check for startupProbe
    Then the startupProbe section is present with httpGet.path "/actuator/health/startup"
