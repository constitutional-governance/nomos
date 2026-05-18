import logging
from mcp.server.fastmcp import FastMCP
from src.config import settings
from src.loaders.base_loader import BaseLoader
from src.models.adr import ADRContent, ADRSummary
from src.models.config import GovernanceConfig
from src.models.constitution import ConstitutionContent
from src.models.convention import NamingConvention, KafkaConventions, CamelConventions, NamingType, RestApiConventions, ServiceConventions
from src.models.check import Check
from src.models.helm import HelmTemplate, HelmServiceType
from src.models.validation import ValidationResult
from src.tools import adr_tools, constitution_tools, convention_tools, check_tools, helm_tools, knowledge_tools
from src.validators import topic as topic_validator, rbac as rbac_validator, sa_naming as sa_validator, schema as schema_validator, rest_path as rest_path_validator, service_name as service_name_validator

logger = logging.getLogger(__name__)

mcp = FastMCP("nomos")

_governance_config: GovernanceConfig | None = None


def _loader() -> BaseLoader:
    from src.loaders.local_loader import LocalLoader
    from src.loaders.github_loader import GitHubLoader
    from src.loaders.team_loader import TeamAwareLoader
    from src.context import _current_team

    if settings.governance_mode == "github":
        base: BaseLoader = GitHubLoader(
            settings.governance_repo_url,
            settings.github_token,
            settings.github_branch,
            settings.cache_ttl_seconds,
        )
    else:
        base = LocalLoader(settings.governance_repo_path)

    team = _current_team.get()
    return TeamAwareLoader(base, team) if team else base


def _config() -> GovernanceConfig:
    global _governance_config
    if _governance_config is None:
        _governance_config = _loader().get_config()
        logger.info("governance config loaded: project=%s", _governance_config.project.name)
    return _governance_config


# ── Discovery tools ────────────────────────────────────────────────────────────

@mcp.tool(description=(
    "List all available constitution domains in this governance repo. "
    "Call this first to discover what domains exist before calling get_constitution()."
))
def list_constitutions() -> list[str]:
    logger.info("list_constitutions")
    return constitution_tools.list_constitution_domains(_loader())


@mcp.tool(description=(
    "List all available check domains in this governance repo. "
    "Call this first to discover what domains have Gherkin checks before calling get_checks()."
))
def list_check_domains() -> list[str]:
    logger.info("list_check_domains")
    return check_tools.list_check_domains(_loader())


@mcp.tool(description=(
    "Return the active validation rules loaded from governance.yml. "
    "Shows what topic prefixes, RBAC roles, resource types, SA envs, and Camel config are in effect. "
    "Call this when you need to understand what is and isn't allowed before generating config."
))
def get_active_rules() -> GovernanceConfig:
    logger.info("get_active_rules")
    return _config()


# ── ADR tools ──────────────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Return the full content of a specific ADR by ID. "
    "Accepts '001', 'ADR-001', or '1'. "
    "Use search_adrs() first if you don't know the exact ID."
))
def get_adr(adr_id: str) -> ADRContent:
    logger.info("get_adr id=%s", adr_id)
    return adr_tools.get_adr(_loader(), adr_id)


@mcp.tool(description=(
    "Full-text search across all ADRs. "
    "Returns a list of summaries (ID, title, status, domain). "
    "Use this before get_adr() when you know the topic but not the ADR number."
))
def search_adrs(query: str) -> list[ADRSummary]:
    logger.info("search_adrs query=%s", query)
    return adr_tools.search_adrs(_loader(), query)


@mcp.tool(description=(
    "List all ADRs with their ID, title, status, and domain. "
    "Use to discover what governance decisions exist before diving into specifics."
))
def list_adrs() -> list[ADRSummary]:
    logger.info("list_adrs")
    return adr_tools.list_adrs(_loader())


# ── Constitution tools ─────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Return the constitution for a domain (e.g. 'global', 'kafka', 'camel'). "
    "Default is 'global'. Call list_constitutions() to see what domains are available. "
    "Always call this before making architectural decisions in the relevant domain."
))
def get_constitution(domain: str = "global") -> ConstitutionContent:
    logger.info("get_constitution domain=%s", domain)
    return constitution_tools.get_constitution(_loader(), domain)


# ── Naming convention tools ────────────────────────────────────────────────────

@mcp.tool(description=(
    "Return the naming pattern and examples for a specific resource type. "
    "Types: kafka_topic, kafka_consumer_group, kstreams_state_store, kstreams_named_operation, "
    "camel_route, camel_application_name, connector_service_account, debug_service_account, "
    "schema_subject, helm_release, deploy_tag."
))
def get_naming_conventions(type: NamingType) -> NamingConvention:
    logger.info("get_naming_conventions type=%s", type)
    return convention_tools.get_naming_convention(type)


@mcp.tool(description=(
    "Return all Kafka conventions in one call: topic naming, consumer groups, state stores, "
    "named operations, schema subjects, valid prefixes, roles, and resource types. "
    "Call this before creating any Kafka topic, RBAC binding, or Schema Registry subject."
))
def get_kafka_conventions() -> KafkaConventions:
    logger.info("get_kafka_conventions")
    return convention_tools.get_kafka_conventions(_config().kafka)


@mcp.tool(description=(
    "Return REST API conventions: resource naming, URL path pattern, versioning strategy, "
    "HTTP method semantics, and error format rules. "
    "Call this before adding or modifying REST endpoints."
))
def get_rest_conventions() -> RestApiConventions:
    logger.info("get_rest_conventions")
    return convention_tools.get_rest_conventions(_config().rest_api)


@mcp.tool(description=(
    "Return microservice naming conventions: name pattern, max length, k8s constraints. "
    "Call this before naming a new service, Helm release, or container image."
))
def get_service_conventions() -> ServiceConventions:
    logger.info("get_service_conventions")
    return convention_tools.get_service_conventions(_config().service)


@mcp.tool(description=(
    "Return all Camel conventions: route ID naming, application name pattern, "
    "consumer group alignment, base class, and parent BOM. "
    "Call this before adding or modifying a Camel route."
))
def get_camel_conventions() -> CamelConventions:
    logger.info("get_camel_conventions")
    return convention_tools.get_camel_conventions(_config().camel)


# ── Check tools ────────────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Return all Gherkin checks for a domain as defined in the governance repo. "
    "Enforced checks have step definitions and run in CI. "
    "Call list_check_domains() to see what domains are available."
))
def get_checks(domain: str) -> list[Check]:
    logger.info("get_checks domain=%s", domain)
    return check_tools.get_checks(_loader(), domain)


@mcp.tool(description=(
    "Return SpringBoot required configuration checks. "
    "Validates application.yml Kafka connectivity, actuator endpoints, "
    "health probes, and prohibited patterns. "
    "Call before modifying any application-docker.yml or application.yml."
))
def get_springboot_checks() -> list[Check]:
    logger.info("get_springboot_checks")
    return check_tools.get_checks(_loader(), "springboot")


# ── Helm template tools ────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Return a ready-to-use Helm values.yml template for a given service type. "
    "Types: 'kafka_consumer', 'kafka_producer', 'kafka_processor' (KStreams with state store), "
    "'camel_integration'. "
    "Replace <CHANGE_ME> placeholders before committing."
))
def get_helm_template(service_type: HelmServiceType) -> HelmTemplate:
    logger.info("get_helm_template service_type=%s", service_type)
    return helm_tools.get_helm_template(service_type)


# ── Validation tools ───────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Validate a topic name against the rules in governance.yml. "
    "Checks segment count, valid prefix, version suffix, lowercase, no hyphens, max length. "
    "Returns valid=true or a list of errors."
))
def validate_topic_name(name: str) -> ValidationResult:
    logger.info("validate_topic_name name=%s", name)
    return topic_validator.validate_topic_name(name, _config().kafka.topic)


@mcp.tool(description=(
    "Validate a single RBAC binding (role_name + resource_type + resource_name) "
    "against the rules in governance.yml. "
    "Use before adding any role_binding to a service account or identity pool."
))
def validate_rbac_binding(
    role_name: str,
    resource_type: str,
    resource_name: str,
) -> ValidationResult:
    logger.info("validate_rbac_binding role=%s type=%s name=%s", role_name, resource_type, resource_name)
    return rbac_validator.validate_rbac_binding(
        role_name, resource_type, resource_name, _config().kafka.rbac
    )


@mcp.tool(description=(
    "Validate a service account name against the naming rules in governance.yml. "
    "Checks prefix, environment suffix, connector direction, and debug suffix."
))
def validate_sa_name(name: str) -> ValidationResult:
    logger.info("validate_sa_name name=%s", name)
    return sa_validator.validate_sa_name(name, _config().kafka.service_account)


@mcp.tool(description=(
    "Validate a Schema Registry entry: format and compatibility_level. "
    "format must be AVRO, JSON, or PROTOBUF. "
    "compatibility_level must be one of the valid SR levels from governance.yml. "
    "Use before adding or modifying any schemas.hcl entry."
))
def validate_schema_entry(format: str, compatibility_level: str) -> ValidationResult:
    logger.info("validate_schema_entry format=%s compatibility_level=%s", format, compatibility_level)
    return schema_validator.validate_schema_entry(format, compatibility_level, _config().kafka.schema_registry)


@mcp.tool(description=(
    "Validate a REST API path against the conventions in governance.yml. "
    "Checks: starts with /, version prefix (/v1/), lowercase kebab-case segments, "
    "no trailing slash, plural resource names. "
    "Returns valid=true or a list of errors and warnings."
))
def validate_rest_path(path: str) -> ValidationResult:
    logger.info("validate_rest_path path=%s", path)
    return rest_path_validator.validate_rest_path(path, _config().rest_api)


@mcp.tool(description=(
    "Validate a microservice name against the conventions in governance.yml. "
    "Checks: lowercase, kebab-case, no underscores, max 63 chars (k8s DNS label limit). "
    "Returns valid=true or a list of errors and warnings."
))
def validate_service_name(name: str) -> ValidationResult:
    logger.info("validate_service_name name=%s", name)
    return service_name_validator.validate_service_name(name, _config().service)


# ── Knowledge tools ────────────────────────────────────────────────────────────

@mcp.tool(description=(
    "List all available knowledge topics in this governance repo. "
    "Call this to discover what AI failure patterns and lessons-learned are documented. "
    "Then call get_knowledge() with a topic name to read the full content."
))
def list_knowledge() -> list[str]:
    logger.info("list_knowledge")
    return knowledge_tools.list_knowledge_topics(_loader())


@mcp.tool(description=(
    "Return the full content of a knowledge document (e.g. 'failures'). "
    "Call list_knowledge() first to see what topics are available. "
    "Always call get_knowledge('failures') before generating Kafka resources — "
    "it documents systematic AI mistakes specific to this platform."
))
def get_knowledge(topic: str) -> str:
    logger.info("get_knowledge topic=%s", topic)
    return knowledge_tools.get_knowledge(_loader(), topic)

