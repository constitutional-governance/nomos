from pydantic import BaseModel, Field


class TopicConfig(BaseModel):
    segment_count: int = 7
    prefixes: list[str] = []
    non_production_prefixes: list[str] = ["dev"]
    max_length: int = 249


class RBACConfig(BaseModel):
    valid_roles: list[str] = []
    valid_resource_types: list[str] = []
    admin_roles: list[str] = ["DeveloperManage"]
    admin_resource_types: list[str] = ["cluster"]
    cluster_resource_name: str = "kafka-cluster"


class SAConfig(BaseModel):
    prefix: str = "sa-"
    valid_envs: list[str] = []
    connector_directions: list[str] = ["source", "sink"]
    debug_suffix: str = "debug"


class CamelConfig(BaseModel):
    base_class: str = "com.example.camel.BaseRouteBuilder"
    parent_bom: str = "com.example:camel-starter-parent:1.0.0"


class KafkaConfig(BaseModel):
    topic: TopicConfig = Field(default_factory=TopicConfig)
    rbac: RBACConfig = Field(default_factory=RBACConfig)
    service_account: SAConfig = Field(default_factory=SAConfig)


class ProjectConfig(BaseModel):
    name: str = "govern-mcp"
    description: str = ""


class GovernanceConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    camel: CamelConfig = Field(default_factory=CamelConfig)
