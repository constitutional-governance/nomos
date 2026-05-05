from behave import given, when, then
from src.validators.topic import validate_topic_name
from src.validators.rbac import validate_rbac_binding
from src.validators.sa_naming import validate_sa_name


@given('the topic name "{name}"')
def step_topic_name(context, name):
    context.validate = lambda: validate_topic_name(name, context.governance_config.kafka.topic)


@given('a role binding with role "{role}" on resource_type "{rtype}" and resource_name "{rname}"')
def step_rbac_binding(context, role, rtype, rname):
    context.validate = lambda: validate_rbac_binding(role, rtype, rname, context.governance_config.kafka.rbac)


@given('a service account named "{name}"')
def step_sa_name(context, name):
    context.validate = lambda: validate_sa_name(name, context.governance_config.kafka.service_account)


@when('I validate it')
def step_validate(context):
    context.result = context.validate()


@then('validation passes')
def step_passes(context):
    assert context.result.valid, \
        f"Expected valid, got errors: {context.result.errors}"


@then('validation fails')
def step_fails(context):
    assert not context.result.valid, \
        "Expected validation to fail, but it passed"


@then('the error contains "{fragment}"')
def step_error_contains(context, fragment):
    assert any(fragment in e for e in context.result.errors), \
        f"No error containing '{fragment}'. Got: {context.result.errors}"


@then('a warning is raised about "{fragment}"')
def step_warning_about(context, fragment):
    assert any(fragment in w for w in context.result.warnings), \
        f"No warning containing '{fragment}'. Got: {context.result.warnings}"
