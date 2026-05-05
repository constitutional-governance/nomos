Feature: Helm required Kubernetes labels
  Reference: ADR-006
  Status: wip — validator pending

  Standard Kubernetes labels (app.kubernetes.io/*) must be present on all
  resources. They are used by platform tooling for cost allocation, incident
  attribution, and network policy selection. Missing labels make it
  impossible to correlate a running pod to its owning team or domain.

  @wip
  Scenario: Deployment template includes app.kubernetes.io/name label
    Given a Helm chart deployment template
    When I check metadata.labels
    Then "app.kubernetes.io/name" is present

  @wip
  Scenario: Deployment template includes app.kubernetes.io/component label
    Given a Helm chart deployment template
    When I check metadata.labels
    Then "app.kubernetes.io/component" is present

  @wip
  Scenario: Deployment template includes app.kubernetes.io/part-of label
    Given a Helm chart deployment template
    When I check metadata.labels
    Then "app.kubernetes.io/part-of" is present and equals the domain name
