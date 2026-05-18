from src.models.convention import (
    NamingConvention, KafkaConventions, CamelConventions, NamingType,
    RestApiConventions, ServiceConventions,
)
from src.models.config import CamelConfig, KafkaConfig, RestApiConfig, ServiceConfig

# ── Kafka ──────────────────────────────────────────────────────────────────────

_KAFKA_TOPIC = NamingConvention(
    type="kafka_topic",
    pattern="{prefix}.{domain}.{group}.{project}.{component}.{name}.{version}",
    examples=[
        "raw.retail.pos.acme.orders.receipt.v1",
        "public.retail.pos.acme.orders.receipt.v2",
        "kstreams.retail.pos.acme.receipt.dlq.v1",
        "landing.retail.pos.acme.lookup.product.v1",
    ],
    adr_ref="ADR-001",
    notes="Exactly 7 dot-separated segments. All lowercase. Version mandatory.",
)

_KAFKA_CONSUMER_GROUP = NamingConvention(
    type="kafka_consumer_group",
    pattern="{prefix}.{domain}.{group}.{project}.{app-name}",
    examples=[
        "kstreams.retail.pos.acme.receipt-processor",
        "kstreams.retail.pos.acme.order-aggregator",
        "kafka.camel.retail.pos.acme.receipt.src.v1",
        "kafka.camel.retail.crm.acme.transaction.sink.v1",
    ],
    adr_ref="ADR-002",
    notes="KStreams → kstreams.* prefix. Camel → kafka.camel.* prefix. Must be set explicitly.",
)

_KSTREAMS_STATE_STORE = NamingConvention(
    type="kstreams_state_store",
    pattern="{entity}.store",
    examples=["order.store", "customer.store", "receipt-dedup.store"],
    adr_ref="ADR-003",
    notes="Dot-separated lowercase. Suffix .store mandatory.",
)

_KSTREAMS_NAMED_OP = NamingConvention(
    type="kstreams_named_operation",
    pattern="{service}.{operation-type}.{entity}.{sequence}",
    examples=[
        "myapp.source.converter.1",
        "myapp.filter.type.1",
        "myapp.leftjoin.order.customer.1",
        "myapp.sink.converter.1",
    ],
    adr_ref="ADR-003",
    notes="Used in Named.as() calls. Sequence is an integer starting at 1.",
)

_SCHEMA_SUBJECT = NamingConvention(
    type="schema_subject",
    pattern="{topic-name}-value  |  {topic-name}-key",
    examples=[
        "raw.retail.pos.acme.orders.receipt.v1-value",
        "public.retail.pos.acme.orders.receipt.v2-value",
    ],
    adr_ref="ADR-007",
    notes="Key subject only when the key carries structured data beyond a plain string.",
)

_CONNECTOR_SA = NamingConvention(
    type="connector_service_account",
    pattern="sa-{system}-connector-{direction}-{type}-{env}",
    examples=[
        "sa-acme-connector-source-jdbc-dev",
        "sa-acme-connector-sink-s3-prod",
    ],
    adr_ref="ADR-009",
    notes="env suffix always last. Map key is used directly as Confluent display_name.",
)

_DEBUG_SA = NamingConvention(
    type="debug_service_account",
    pattern="sa-{system}-{component}-debug",
    examples=["sa-retail-acme-dev-debug"],
    adr_ref="ADR-008",
    notes="Dev only. Must never appear in prod.",
)

_DEPLOY_TAG = NamingConvention(
    type="deploy_tag",
    pattern="{domain_path}@v{major}.{minor}.{patch}",
    examples=["retail/pos/acme/receipt@v0.1.0", "retail/pos/acme/orders@v1.3.2"],
    adr_ref="ADR-011",
)

# ── Camel ──────────────────────────────────────────────────────────────────────

_CAMEL_ROUTE = NamingConvention(
    type="camel_route",
    pattern="{verb}{Entity} | {entity}ParallelProcessing | {action}Scheduler | sent{Entity}To{Destination}",
    examples=[
        "apiScheduler",
        "getOrders",
        "aggregateReceipts",
        "sentOrderToKafka",
        "evictCacheCustomer",
    ],
    adr_ref="ADR-004",
    notes="camelCase. Defined as constants in Constants.java. No magic strings in routes.",
)

_CAMEL_APP_NAME = NamingConvention(
    type="camel_application_name",
    pattern="kafka-camel-{repo-name}",
    examples=[
        "kafka-camel-retail-pos-acme-receipt-src",
        "kafka-camel-retail-crm-acme-transactions-sink",
    ],
    adr_ref="ADR-004",
    notes="Set in camel.main.name in application-docker.yml.",
)

# ── Helm ───────────────────────────────────────────────────────────────────────

_HELM_RELEASE = NamingConvention(
    type="helm_release",
    pattern="Values file at pipelines/cd/{env}/values.yml",
    examples=[
        "pipelines/cd/dev/values.yml",
        "pipelines/cd/prod/values.yml",
    ],
    adr_ref="ADR-006",
    notes="Shared library chart — no Chart.yaml per service. Extension is .yml not .yaml.",
)

_NAMING_MAP: dict[NamingType, NamingConvention] = {
    "kafka_topic": _KAFKA_TOPIC,
    "kafka_consumer_group": _KAFKA_CONSUMER_GROUP,
    "kstreams_state_store": _KSTREAMS_STATE_STORE,
    "kstreams_named_operation": _KSTREAMS_NAMED_OP,
    "schema_subject": _SCHEMA_SUBJECT,
    "connector_service_account": _CONNECTOR_SA,
    "debug_service_account": _DEBUG_SA,
    "deploy_tag": _DEPLOY_TAG,
    "camel_route": _CAMEL_ROUTE,
    "camel_application_name": _CAMEL_APP_NAME,
    "helm_release": _HELM_RELEASE,
}


def get_naming_convention(naming_type: NamingType) -> NamingConvention:
    return _NAMING_MAP[naming_type]


_ALL_PREFIX_SEMANTICS: dict[str, str] = {
    "raw": "Direct source ingestion — infinite retention — source of truth",
    "public": "Cross-domain canonical events — 30d default",
    "ready": "Aggregated / enriched for downstream — 30d default",
    "private": "Internal domain — not shared with other domains",
    "kstreams": "KStreams internals: changelog, repartition, DLQ",
    "kcamel": "Camel K internal routing and DLQ",
    "sink": "Destined for external sink connectors",
    "landing": "External-agent ingest zone — 7d retention",
    "dev": "Dev-only ephemeral — 1d retention — MUST NOT exist in prod",
}


def get_kafka_conventions(kafka_config: KafkaConfig | None = None) -> KafkaConventions:
    config = kafka_config or KafkaConfig()
    prefixes = config.topic.prefixes or list(_ALL_PREFIX_SEMANTICS.keys())
    return KafkaConventions(
        topic_naming=_KAFKA_TOPIC,
        consumer_group_naming=_KAFKA_CONSUMER_GROUP,
        state_store_naming=_KSTREAMS_STATE_STORE,
        named_operation_naming=_KSTREAMS_NAMED_OP,
        schema_subject_naming=_SCHEMA_SUBJECT,
        valid_prefixes=prefixes,
        valid_roles=config.rbac.valid_roles or ["DeveloperRead", "DeveloperWrite", "ResourceOwner", "DeveloperManage"],
        valid_resource_types=config.rbac.valid_resource_types or ["topic", "group", "transactional-id", "cluster"],
        prefix_semantics={p: _ALL_PREFIX_SEMANTICS[p] for p in prefixes if p in _ALL_PREFIX_SEMANTICS},
    )


def get_camel_conventions(camel_config: CamelConfig | None = None) -> CamelConventions:
    config = camel_config or CamelConfig()
    return CamelConventions(
        route_id_naming=_CAMEL_ROUTE,
        application_name=_CAMEL_APP_NAME,
        consumer_group=_KAFKA_CONSUMER_GROUP,
        base_class=config.base_class,
        parent_bom=config.parent_bom,
    )


# ── REST API ───────────────────────────────────────────────────────────────────

_REST_RESOURCE = NamingConvention(
    type="rest_resource",
    pattern="/{version}/{resource}  |  /{version}/{resource}/{id}  |  /{version}/{resource}/{id}/{sub-resource}",
    examples=[
        "/v1/orders",
        "/v1/orders/{orderId}",
        "/v1/orders/{orderId}/items",
        "/v1/customers/{customerId}/addresses",
    ],
    adr_ref="",
    notes="Plural nouns. Kebab-case. Version prefix mandatory. No verbs in paths — use HTTP methods.",
)

_REST_METHOD_SEMANTICS: dict[str, str] = {
    "GET": "Read — idempotent, no side effects, safe to retry",
    "POST": "Create — not idempotent, generates a new resource",
    "PUT": "Replace — idempotent, replaces the full resource",
    "PATCH": "Update — partial modification, idempotent if designed correctly",
    "DELETE": "Remove — idempotent (deleting a non-existent resource returns 404 or 204)",
}

_REST_NOTES = [
    "Versioning is path-based (/v1/, /v2/) — not query parameter or Accept header.",
    "Resource names are plural nouns — /orders not /order, /customers not /customer.",
    "No verbs in paths — use the HTTP method to express the action.",
    "Error responses use a structured body: { code, message, details }.",
    "Pagination uses cursor or offset/limit query params — not path segments.",
    "IDs in paths are opaque strings — do not expose internal database IDs as integers.",
]


def get_rest_conventions(config: RestApiConfig | None = None) -> RestApiConventions:
    c = config or RestApiConfig()
    return RestApiConventions(
        resource_naming=_REST_RESOURCE,
        path_pattern=f"/{c.version_prefix}{{n}}/{{resource}}[/{{id}}[/{{sub-resource}}]]",
        versioning_strategy=c.versioning_strategy,
        method_semantics=_REST_METHOD_SEMANTICS,
        notes=_REST_NOTES,
    )


# ── Microservice ───────────────────────────────────────────────────────────────

_SERVICE_NAME = NamingConvention(
    type="microservice_name",
    pattern="{domain}-{system}  |  {domain}-{system}-{role}",
    examples=[
        "retail-receipt-processor",
        "sales-order-api",
        "payments-gateway",
        "retail-pos-acme-connector",
    ],
    adr_ref="",
    notes="Lowercase kebab-case. Max 63 chars (k8s DNS label). No underscores.",
)

_SERVICE_NOTES = [
    "Name is used as Helm release name, k8s Deployment name, and container image name — must be DNS-safe.",
    "Max 63 characters — Kubernetes DNS label limit.",
    "No underscores — use hyphens.",
    "Follow {domain}-{system} at minimum; add -{role} suffix when multiple components share the same system.",
    "Image tag follows the deploy tag convention: {service-path}@v{semver}.",
]


def get_service_conventions(config: ServiceConfig | None = None) -> ServiceConventions:
    c = config or ServiceConfig()
    return ServiceConventions(
        service_name=_SERVICE_NAME,
        name_pattern=c.name_pattern,
        max_length=c.max_length,
        notes=_SERVICE_NOTES,
    )
