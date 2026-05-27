from pydantic import BaseModel, Field


class RolloutConfig(BaseModel):
    """Controls gradual rollout of a governance rule to specific teams.

    phase: "canary" — rule is only enforced for teams listed in ``teams``.
           All other teams receive a warning instead of an error.
    phase: "stable" (default) — rule is enforced for every team (normal behaviour).
    """
    phase: str = "stable"   # "stable" | "canary"
    teams: list[str] = []   # teams under full enforcement during canary phase


class TopicConfig(BaseModel):
    segment_count: int = 7
    prefixes: list[str] = []
    non_production_prefixes: list[str] = ["dev"]
    max_length: int = 249
    rollout: RolloutConfig | None = None


class RBACConfig(BaseModel):
    valid_roles: list[str] = []
    valid_resource_types: list[str] = []
    admin_roles: list[str] = ["DeveloperManage"]
    admin_resource_types: list[str] = ["cluster"]
    cluster_resource_name: str = "kafka-cluster"
    rollout: RolloutConfig | None = None


class SAConfig(BaseModel):
    prefix: str = "sa-"
    valid_envs: list[str] = []
    connector_directions: list[str] = ["source", "sink"]
    debug_suffix: str = "debug"
    rollout: RolloutConfig | None = None


class SchemaConfig(BaseModel):
    valid_formats: list[str] = ["AVRO", "JSON", "PROTOBUF"]
    valid_compatibility_levels: list[str] = [
        "BACKWARD", "BACKWARD_TRANSITIVE",
        "FORWARD", "FORWARD_TRANSITIVE",
        "FULL", "FULL_TRANSITIVE",
        "NONE",
    ]
    default_format: str = "AVRO"
    default_compatibility_level: str = "BACKWARD"
    rollout: RolloutConfig | None = None


class CamelConfig(BaseModel):
    base_class: str = "com.example.camel.BaseRouteBuilder"
    parent_bom: str = "com.example:camel-starter-parent:1.0.0"


class KafkaConfig(BaseModel):
    topic: TopicConfig = Field(default_factory=TopicConfig)
    rbac: RBACConfig = Field(default_factory=RBACConfig)
    service_account: SAConfig = Field(default_factory=SAConfig)
    schema_registry: SchemaConfig = Field(default_factory=SchemaConfig)


class RestApiConfig(BaseModel):
    path_style: str = "kebab-case"
    versioning_strategy: str = "path"
    version_prefix: str = "v"
    require_version: bool = True
    allowed_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    rollout: RolloutConfig | None = None


class ServiceConfig(BaseModel):
    name_pattern: str = r"^[a-z][a-z0-9-]{1,61}[a-z0-9]$"
    max_length: int = 63
    rollout: RolloutConfig | None = None


class ProjectConfig(BaseModel):
    name: str = "govern-mcp"
    description: str = ""


class GovernanceConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    camel: CamelConfig = Field(default_factory=CamelConfig)
    rest_api: RestApiConfig = Field(default_factory=RestApiConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)
