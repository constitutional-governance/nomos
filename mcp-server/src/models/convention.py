from pydantic import BaseModel
from typing import Literal

NamingType = Literal[
    "kafka_topic",
    "kafka_consumer_group",
    "kstreams_state_store",
    "kstreams_named_operation",
    "camel_route",
    "camel_application_name",
    "connector_service_account",
    "debug_service_account",
    "schema_subject",
    "helm_release",
    "deploy_tag",
    "rest_resource",
    "microservice_name",
]


class NamingConvention(BaseModel):
    type: NamingType
    pattern: str
    examples: list[str]
    adr_ref: str
    notes: str = ""


class KafkaConventions(BaseModel):
    topic_naming: NamingConvention
    consumer_group_naming: NamingConvention
    state_store_naming: NamingConvention
    named_operation_naming: NamingConvention
    schema_subject_naming: NamingConvention
    valid_prefixes: list[str]
    valid_roles: list[str]
    valid_resource_types: list[str]
    prefix_semantics: dict[str, str]


class CamelConventions(BaseModel):
    route_id_naming: NamingConvention
    application_name: NamingConvention
    consumer_group: NamingConvention
    base_class: str
    parent_bom: str


class RestApiConventions(BaseModel):
    resource_naming: NamingConvention
    path_pattern: str
    versioning_strategy: str
    method_semantics: dict[str, str]
    notes: list[str]


class ServiceConventions(BaseModel):
    service_name: NamingConvention
    name_pattern: str
    max_length: int
    notes: list[str]
