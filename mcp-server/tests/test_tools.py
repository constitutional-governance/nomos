from pathlib import Path
from src.loaders.local_loader import LocalLoader
from src.tools import adr_tools, constitution_tools, convention_tools, check_tools

REPO_ROOT = Path(__file__).parent.parent.parent


def loader():
    return LocalLoader(REPO_ROOT)


# ── ADR tools ──────────────────────────────────────────────────────────────────

def test_list_adrs_returns_all():
    adrs = adr_tools.list_adrs(loader())
    assert len(adrs) >= 1
    ids = {a.id for a in adrs}
    assert "001" in ids


def test_get_adr_by_plain_id():
    adr = adr_tools.get_adr(loader(), "001")
    assert adr.id == "001"
    assert adr.status in ("Accepted", "Draft", "Proposed")


def test_get_adr_by_prefixed_id():
    adr = adr_tools.get_adr(loader(), "ADR-002")
    assert adr.id == "002"


def test_get_adr_missing_raises():
    try:
        adr_tools.get_adr(loader(), "999")
        assert False
    except FileNotFoundError:
        pass


def test_search_adrs_finds_by_keyword():
    results = adr_tools.search_adrs(loader(), "consumer group")
    assert any("002" == r.id for r in results)


def test_search_adrs_no_match_returns_empty():
    results = adr_tools.search_adrs(loader(), "xxxxxxnotfound")
    assert results == []


# ── Constitution tools ─────────────────────────────────────────────────────────

def test_get_global_constitution():
    c = constitution_tools.get_constitution(loader(), "global")
    assert len(c.content) > 0
    assert c.domain == "global"


def test_get_kafka_constitution():
    c = constitution_tools.get_constitution(loader(), "kafka")
    assert "kafka" in c.content.lower()


def test_get_camel_constitution():
    c = constitution_tools.get_constitution(loader(), "camel")
    assert "camel" in c.content.lower()


# ── Convention tools ───────────────────────────────────────────────────────────

def test_get_kafka_topic_convention():
    conv = convention_tools.get_naming_convention("kafka_topic")
    assert "{prefix}" in conv.pattern
    assert len(conv.examples) >= 2
    assert conv.adr_ref == "ADR-001"


def test_get_kafka_conventions_all_fields():
    from src.loaders.local_loader import LocalLoader
    from pathlib import Path
    cfg = LocalLoader(Path(__file__).parent.parent.parent).get_config()
    kc = convention_tools.get_kafka_conventions(cfg.kafka)
    assert "raw" in kc.valid_prefixes
    assert "DeveloperRead" in kc.valid_roles
    assert len(kc.prefix_semantics) >= 1
    assert set(kc.valid_prefixes) == set(kc.prefix_semantics.keys()) | (set(kc.valid_prefixes) - set(kc.prefix_semantics.keys()))


def test_get_camel_conventions():
    cc = convention_tools.get_camel_conventions()
    assert cc.base_class
    assert cc.parent_bom


def test_get_camel_conventions_reads_config():
    from src.models.config import CamelConfig
    cfg = CamelConfig(base_class="com.test.MyBase", parent_bom="com.test:my-bom:1.0.0")
    cc = convention_tools.get_camel_conventions(cfg)
    assert cc.base_class == "com.test.MyBase"
    assert cc.parent_bom == "com.test:my-bom:1.0.0"


# ── Discovery tools ────────────────────────────────────────────────────────────

def test_list_constitution_domains():
    domains = constitution_tools.list_constitution_domains(loader())
    assert "global" in domains
    assert "kafka" in domains
    assert "camel" in domains


def test_list_check_domains():
    domains = check_tools.list_check_domains(loader())
    assert "kafka" in domains
    assert len(domains) >= 1


def test_get_kafka_conventions_prefix_semantics_matches_prefixes():
    from pathlib import Path
    from src.loaders.local_loader import LocalLoader
    cfg = LocalLoader(REPO_ROOT).get_config()
    kc = convention_tools.get_kafka_conventions(cfg.kafka)
    for prefix in kc.prefix_semantics:
        assert prefix in kc.valid_prefixes


# ── Check tools ────────────────────────────────────────────────────────────────

def test_get_kafka_checks():
    checks = check_tools.get_checks(loader(), "kafka")
    assert len(checks) >= 3
    assert all(c.domain == "kafka" for c in checks)
    assert any(c.status == "enforced" for c in checks)  # at least some are enforced


def test_get_camel_checks_are_draft():
    checks = check_tools.get_checks(loader(), "camel")
    assert len(checks) >= 2
    assert all(c.status == "draft" for c in checks)  # camel features have no @enforced scenarios


def test_get_springboot_checks():
    checks = check_tools.get_checks(loader(), "springboot")
    assert len(checks) >= 3
    assert all(c.domain == "springboot" for c in checks)


# ── Helm template tests ────────────────────────────────────────────────────────

def test_get_helm_template_kafka_processor():
    from src.tools import helm_tools
    t = helm_tools.get_helm_template("kafka_processor")
    assert t.service_type == "kafka_processor"
    assert "STATE_DIR" in t.values_yml
    assert len(t.notes) >= 1


def test_get_helm_template_camel_integration():
    from src.tools import helm_tools
    t = helm_tools.get_helm_template("camel_integration")
    assert t.service_type == "camel_integration"
    assert "JAVA_OPTS" in t.values_yml
    assert "startupProbe" in t.values_yml


def test_get_helm_template_kafka_consumer():
    from src.tools import helm_tools
    t = helm_tools.get_helm_template("kafka_consumer")
    assert t.service_type == "kafka_consumer"
    assert "STATE_DIR" not in t.values_yml


def test_get_helm_template_kafka_producer():
    from src.tools import helm_tools
    t = helm_tools.get_helm_template("kafka_producer")
    assert t.service_type == "kafka_producer"
    assert "AUTO_OFFSET_RESET" not in t.values_yml
