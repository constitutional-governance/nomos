Feature: RBAC role binding constraints
  Reference: ADR-002
  Status: enforced

  DeveloperManage grants admin-level control (create, delete, alter config).
  Restricting it to resource_type 'cluster' prevents accidental topic-level
  admin grants that would let a service account delete or reconfigure topics
  it only needs to read or write — violating the least-privilege model.

  resource_type 'cluster' always refers to the single Confluent Cloud Kafka
  cluster. Its resource_name is always 'kafka-cluster' — any other value
  indicates a copy-paste error or misconfiguration.

  @enforced
  Scenario: DeveloperRead on a topic is valid
    Given a role binding with role "DeveloperRead" on resource_type "topic" and resource_name "raw.retail.*"
    When I validate it
    Then validation passes

  @enforced
  Scenario: ResourceOwner on a consumer group is valid
    Given a role binding with role "ResourceOwner" on resource_type "group" and resource_name "kstreams.retail.*"
    When I validate it
    Then validation passes

  @enforced
  Scenario: DeveloperManage on the cluster is valid
    Given a role binding with role "DeveloperManage" on resource_type "cluster" and resource_name "kafka-cluster"
    When I validate it
    Then validation passes

  @enforced
  Scenario: DeveloperManage on a topic is rejected — would grant topic delete rights
    Given a role binding with role "DeveloperManage" on resource_type "topic" and resource_name "raw.retail.*"
    When I validate it
    Then validation fails
    And the error contains "DeveloperManage is only valid on resource_type 'cluster'"

  @enforced
  Scenario: DeveloperManage on a consumer group is rejected
    Given a role binding with role "DeveloperManage" on resource_type "group" and resource_name "kstreams.retail.*"
    When I validate it
    Then validation fails
    And the error contains "DeveloperManage is only valid on resource_type 'cluster'"

  @enforced
  Scenario: cluster resource_name other than kafka-cluster is a misconfiguration
    Given a role binding with role "DeveloperManage" on resource_type "cluster" and resource_name "my-cluster"
    When I validate it
    Then validation fails
    And the error contains "kafka-cluster"

  @enforced
  Scenario: Unknown role name is rejected
    Given a role binding with role "SuperAdmin" on resource_type "topic" and resource_name "raw.retail.*"
    When I validate it
    Then validation fails
    And the error contains "invalid role_name"

  @enforced
  Scenario: Unknown resource type is rejected
    Given a role binding with role "DeveloperRead" on resource_type "queue" and resource_name "raw.retail.*"
    When I validate it
    Then validation fails
    And the error contains "invalid resource_type"
