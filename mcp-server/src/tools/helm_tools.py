from src.models.helm import HelmTemplate, HelmServiceType

_KAFKA_CONSUMER = HelmTemplate(
    service_type="kafka_consumer",
    description="Plain Kafka consumer — reads from topics, no state store, no Camel.",
    values_yml="""\
# Azure Container registry identifier: default
# replicas: 1

envVariables:
  - name: "LOGGING_LEVEL_ROOT"
    value: "WARN"
  - name: "LOGGING_AVOLTA_LEVEL"
    value: "INFO"
  - name: "AUTO_OFFSET_RESET"
    value: "latest"
  - name: "AUTO_REGISTER_SCHEMAS"
    value: "false"
  - name: "USE_LATEST_VERSION"
    value: "true"
  - name: "SASL_JAAS_CONFIG_USERNAME"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SASL_JAAS_CONFIG_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password
  - name: "SASL_JAAS_CONFIG_SERVICE_NAME"
    value: "kafka"
  - name: "SSL_TRUSTSTORE_LOCATION"
    value: "/mnt/secrets/kafka/truststore.jks"
  - name: "SSL_TRUSTSTORE_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: truststore.password
  - name: "SCHEMA_REGISTRY_AUTH_USER"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SCHEMA_REGISTRY_AUTH_TOKEN"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password

livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 3
  periodSeconds: 10
  timeoutSeconds: 5
  initialDelaySeconds: 1

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  failureThreshold: 30
  periodSeconds: 5
  timeoutSeconds: 5
  initialDelaySeconds: 1

secrets:
  - name: "kafka"
    mountRootPath: "/mnt/secrets"
    csi:
      objects:
        - objectName: <CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>
          objectAlias: kafka-user.password
        - objectName: ssl-truststore-kafka-jks
          objectAlias: truststore.jks
          objectEncoding: base64
        - objectName: ssl-truststore-kafka-password
          objectAlias: truststore.password

resources:
  requests:
    memory: 256Mi
  limits:
    memory: 512Mi
""",
    notes=[
        "Replace all <CHANGE_ME> placeholders before committing.",
        "SASL_JAAS_CONFIG_USERNAME and SCHEMA_REGISTRY_AUTH_USER must match the Kafka2 service account name.",
        "Secret objectName in Key Vault must match the exact KV entry name (usually the SA name).",
        "Add BOOTSTRAP_SERVERS only if the service does not use the in-cluster default (kafka-bootstrap.confluent.svc.cluster.local:9092).",
    ],
)

_KAFKA_PRODUCER = HelmTemplate(
    service_type="kafka_producer",
    description="Plain Kafka producer — writes to topics, no consumer group, no state store.",
    values_yml="""\
# Azure Container registry identifier: default
# replicas: 1

envVariables:
  - name: "LOGGING_LEVEL_ROOT"
    value: "WARN"
  - name: "LOGGING_AVOLTA_LEVEL"
    value: "INFO"
  - name: "AUTO_REGISTER_SCHEMAS"
    value: "false"
  - name: "USE_LATEST_VERSION"
    value: "true"
  - name: "SASL_JAAS_CONFIG_USERNAME"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SASL_JAAS_CONFIG_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password
  - name: "SASL_JAAS_CONFIG_SERVICE_NAME"
    value: "kafka"
  - name: "SSL_TRUSTSTORE_LOCATION"
    value: "/mnt/secrets/kafka/truststore.jks"
  - name: "SSL_TRUSTSTORE_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: truststore.password
  - name: "SCHEMA_REGISTRY_AUTH_USER"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SCHEMA_REGISTRY_AUTH_TOKEN"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password

livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 3
  periodSeconds: 10
  timeoutSeconds: 5
  initialDelaySeconds: 1

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  failureThreshold: 30
  periodSeconds: 5
  timeoutSeconds: 5
  initialDelaySeconds: 1

secrets:
  - name: "kafka"
    mountRootPath: "/mnt/secrets"
    csi:
      objects:
        - objectName: <CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>
          objectAlias: kafka-user.password
        - objectName: ssl-truststore-kafka-jks
          objectAlias: truststore.jks
          objectEncoding: base64
        - objectName: ssl-truststore-kafka-password
          objectAlias: truststore.password

resources:
  requests:
    memory: 128Mi
  limits:
    memory: 256Mi
""",
    notes=[
        "No AUTO_OFFSET_RESET — producers do not have a consumer group.",
        "Replace all <CHANGE_ME> placeholders before committing.",
        "SASL_JAAS_CONFIG_USERNAME must match the Kafka2 service account name.",
    ],
)

_KAFKA_PROCESSOR = HelmTemplate(
    service_type="kafka_processor",
    description="KStreams processor — stateful topology with local state store on persistent volume.",
    values_yml="""\
# Azure Container registry identifier: default
# replicas: 1

envVariables:
  - name: "LOGGING_LEVEL_ROOT"
    value: "WARN"
  - name: "LOGGING_AVOLTA_LEVEL"
    value: "INFO"
  - name: "AUTO_OFFSET_RESET"
    value: "latest"
  - name: "AUTO_REGISTER_SCHEMAS"
    value: "false"
  - name: "USE_LATEST_VERSION"
    value: "true"
  - name: "SASL_JAAS_CONFIG_USERNAME"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SASL_JAAS_CONFIG_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password
  - name: "SASL_JAAS_CONFIG_SERVICE_NAME"
    value: "kafka"
  - name: "SSL_TRUSTSTORE_LOCATION"
    value: "/mnt/secrets/kafka/truststore.jks"
  - name: "SSL_TRUSTSTORE_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: truststore.password
  - name: "SCHEMA_REGISTRY_AUTH_USER"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>"
  - name: "SCHEMA_REGISTRY_AUTH_TOKEN"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password
  - name: "STATE_DIR"
    value: "/mnt/data/store"
  - name: "SPRING_KAFKA_PROPERTIES_ACK"
    value: "all"
  - name: "SPRING_KAFKA_PROPERTIES_REPLICATION_FACTOR"
    value: "3"
  - name: "STATIC_MEMBERSHIP"
    value: "false"
  - name: "MAX_POLL_RECORDS"
    value: "50000"
  - name: "STANDBY_REPLICAS"
    value: "0"
  - name: "SESSION_TIMEOUT"
    value: "30000"
  - name: "HEARTBEAT_INTERVAL"
    value: "300"
  - name: "LINGER"
    value: "0"
  - name: "REQUEST_TIMEOUT"
    value: "60000"
  - name: "NUM_THREADS"
    value: "1"
  - name: "CACHE_MAX_BYTES_BUFFERING"
    value: "1024"
  - name: "METRICS_RECORDING_LEVEL"
    value: "TRACE"

# KStreams liveness check hits the kstreams health group
livenessProbe:
  httpGet:
    path: /actuator/health/kstreams
    port: 8080
  initialDelaySeconds: 90
  periodSeconds: 5

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 90
  periodSeconds: 5

secrets:
  - name: "kafka"
    mountRootPath: "/mnt/secrets"
    csi:
      objects:
        - objectName: <CHANGE_ME: S-UN-DOMAIN-SYSTEM-STREAM>
          objectAlias: kafka-user.password
        - objectName: ssl-truststore-kafka-jks
          objectAlias: truststore.jks
          objectEncoding: base64
        - objectName: ssl-truststore-kafka-password
          objectAlias: truststore.password

resources:
  requests:
    memory: 256Mi
  limits:
    memory: 512Mi

# Persistent volume for KStreams state store
volumes:
  - name: "store"
    mountRootPath: "/mnt/data"
    storageSize: 1G
    storageAccessModes:
      - accessMode: "ReadWriteOnce"
    storageClassName: "kafka-standardssd-retain"
""",
    notes=[
        "STATE_DIR must match the mountRootPath/name of the volumes entry.",
        "storageClassName must be kafka-standardssd-retain — do not change.",
        "livenessProbe targets /actuator/health/kstreams (the kstreams health group), not /liveness.",
        "initialDelaySeconds 90 is required — KStreams state store restore takes time on pod restart.",
        "Replace all <CHANGE_ME> placeholders before committing.",
    ],
)

_CAMEL_INTEGRATION = HelmTemplate(
    service_type="camel_integration",
    description="Apache Camel integration — event-driven route with startup/liveness/readiness probes.",
    values_yml="""\
# Azure Container registry identifier: default
# replicas: 1

envVariables:
  - name: "JAVA_OPTS"
    value: "--add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED"
  - name: "LOGGING_LEVEL_ROOT"
    value: "WARN"
  - name: "LOGGING_AVOLTA_LEVEL_ROOT"
    value: "INFO"
  - name: "AUTO_OFFSET_RESET"
    value: "latest"
  - name: "AUTO_REGISTER_SCHEMAS"
    value: "false"
  - name: "USE_LATEST_VERSION"
    value: "true"
  - name: "SASL_JAAS_CONFIG_USERNAME"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-CONSUMER>"
  - name: "SASL_JAAS_CONFIG_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password
  - name: "SASL_JAAS_CONFIG_SERVICE_NAME"
    value: "kafka"
  - name: "SSL_TRUSTSTORE_LOCATION"
    value: "/mnt/secrets/kafka/truststore.jks"
  - name: "SSL_TRUSTSTORE_PASSWORD"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: truststore.password
  - name: "SSL_TRUSTSTORE_TYPE"
    value: "pkcs12"
  - name: "SCHEMA_REGISTRY_AUTH_USER"
    value: "<CHANGE_ME: S-UN-DOMAIN-SYSTEM-CONSUMER>"
  - name: "SCHEMA_REGISTRY_AUTH_TOKEN"
    secretKeyRefSecretName: kafka
    secretKeyRefKey: kafka-user.password

startupProbe:
  httpGet:
    path: /actuator/health/startup
    port: 8080
  failureThreshold: 3
  periodSeconds: 20
  timeoutSeconds: 5
  initialDelaySeconds: 40

livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 3
  periodSeconds: 10
  timeoutSeconds: 5
  initialDelaySeconds: 1

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  failureThreshold: 30
  periodSeconds: 5
  timeoutSeconds: 5
  initialDelaySeconds: 1

secrets:
  - name: "kafka"
    mountRootPath: "/mnt/secrets"
    csi:
      objects:
        - objectName: <CHANGE_ME: S-UN-DOMAIN-SYSTEM-CONSUMER>
          objectAlias: kafka-user.password
        - objectName: ssl-truststore-kafka-jks
          objectAlias: truststore.jks
          objectEncoding: base64
        - objectName: ssl-truststore-kafka-password
          objectAlias: truststore.password

resources:
  requests:
    memory: 300Mi
  limits:
    memory: 512Mi
""",
    notes=[
        "JAVA_OPTS with --add-opens is required for Camel serialization — do not remove.",
        "Camel uses startupProbe in addition to liveness and readiness — KStreams does not.",
        "SSL_TRUSTSTORE_TYPE pkcs12 required for Camel; KStreams services use JKS without explicit type.",
        "Replace all <CHANGE_ME> placeholders before committing.",
        "For sink integrations with external systems (SF, REST), add extra secrets block for the target credentials.",
    ],
)

_TEMPLATES: dict[str, HelmTemplate] = {
    "kafka_consumer": _KAFKA_CONSUMER,
    "kafka_producer": _KAFKA_PRODUCER,
    "kafka_processor": _KAFKA_PROCESSOR,
    "camel_integration": _CAMEL_INTEGRATION,
}


def get_helm_template(service_type: HelmServiceType) -> HelmTemplate:
    return _TEMPLATES[service_type]
