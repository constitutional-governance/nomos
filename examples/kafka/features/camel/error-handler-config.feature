Feature: Apache Camel error handler configuration
  Reference: ADR-004
  Status: wip — validator pending

  Every Camel route must declare explicit error handling. Routes that rely
  on the default error handler will stop on the first exception and block
  the consumer thread indefinitely — causing lag to accumulate on the topic
  until the pod is manually restarted.

  Platform standard: dead letter channel pointing to a .dlq.v1 topic,
  with configurable redelivery delay and max redeliveries from environment
  variables (BACKOFF_MAX_REDELIVERIES, BACKOFF_INITIAL_REDELIVERY_DELAY_MS).

  @wip
  Scenario: Route declares an error handler
    Given a Camel route definition
    When I check for error handler configuration
    Then the route declares onException or errorHandler(), not the default handler

  @wip
  Scenario: Dead letter channel points to a .dlq.v1 topic
    Given a Camel route with a dead letter channel
    When I check the dead letter URI
    Then it points to a topic ending in ".dlq.v1"

  @wip
  Scenario: Redelivery settings come from environment variables
    Given a Camel route with redelivery configuration
    When I check maximumRedeliveries and redeliveryDelay
    Then both reference environment variables (BACKOFF_MAX_REDELIVERIES, BACKOFF_INITIAL_REDELIVERY_DELAY_MS)
