"""
nomos-validate — CLI validator, usable as pre-commit hook or in CI pipelines.

Local mode (reads governance.yml from GOVERNANCE_REPO_PATH):
    nomos-validate topic "raw.payments.pos.acme.checkout.receipt.v1"
    nomos-validate rbac DeveloperRead topic "raw.payments.*"
    nomos-validate sa "sa-payments-connector-source-jdbc-prod"
    nomos-validate schema AVRO BACKWARD
    nomos-validate rest-path "/v1/orders/{orderId}/items"
    nomos-validate service-name "payments-checkout-api"

Remote mode (delegates to a shared Nomos server):
    nomos-validate --server https://governance.acme.com topic "raw.payments..."
    nomos-validate --server https://governance.acme.com rbac DeveloperRead topic "raw.*"
    nomos-validate --server https://governance.acme.com sa "sa-payments-..."
    nomos-validate --server https://governance.acme.com schema AVRO BACKWARD

Canary rollout (pass team to apply rollout rules):
    nomos-validate --team payments topic "raw.payments.checkout.v1"
    nomos-validate --server https://governance.acme.com --team payments sa "sa-..."

Exit code: 0 if valid (or advisory warnings only), 1 if any errors.
"""
import sys
from pathlib import Path


def _parse_flags(argv: list[str]) -> tuple[str | None, str | None, list[str]]:
    """Extract --server and --team flags, return (server_url, team, remaining_args)."""
    server_url = None
    team = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--server" and i + 1 < len(argv):
            server_url = argv[i + 1].rstrip("/")
            i += 2
        elif argv[i] == "--team" and i + 1 < len(argv):
            team = argv[i + 1]
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    return server_url, team, rest


def _print_result(valid: bool, errors: list, warnings: list, label: str) -> bool:
    if valid:
        print(f"OK  {label}")
        for w in warnings:
            print(f"    WARNING: {w}")
    else:
        print(f"ERR {label}")
        for e in errors:
            print(f"    {e}")
    return valid


# ── Remote mode ────────────────────────────────────────────────────────────────

def _remote(server_url: str, team: str | None, args: list[str]) -> int:
    import httpx

    if not args:
        print(__doc__)
        return 0

    command = args[0]
    endpoint_map = {
        "topic":        "/validate/topic",
        "rbac":         "/validate/rbac",
        "sa":           "/validate/sa",
        "schema":       "/validate/schema",
        "rest-path":    "/validate/rest-path",
        "service-name": "/validate/service-name",
    }

    if command not in endpoint_map:
        print(f"Unknown command '{command}'. Available: {', '.join(endpoint_map)}")
        return 1

    url = server_url + endpoint_map[command]

    def _post(payload: dict) -> dict:
        if team:
            payload["team"] = team
        r = httpx.post(url, json=payload, timeout=10)
        return r.json()

    try:
        if command == "topic":
            if len(args) < 2:
                print("Usage: nomos-validate [--server URL] [--team NAME] topic <name> [<name> ...]")
                return 1
            ok = True
            for name in args[1:]:
                data = _post({"name": name})
                if not _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), name):
                    ok = False
            return 0 if ok else 1

        elif command == "rbac":
            if len(args) < 4:
                print("Usage: nomos-validate [--server URL] [--team NAME] rbac <role_name> <resource_type> <resource_name>")
                return 1
            data = _post({"role_name": args[1], "resource_type": args[2], "resource_name": args[3]})
            label = f"{args[1]} / {args[2]} / {args[3]}"
            return 0 if _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), label) else 1

        elif command == "sa":
            if len(args) < 2:
                print("Usage: nomos-validate [--server URL] [--team NAME] sa <name> [<name> ...]")
                return 1
            ok = True
            for name in args[1:]:
                data = _post({"name": name})
                if not _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), name):
                    ok = False
            return 0 if ok else 1

        elif command == "schema":
            if len(args) < 3:
                print("Usage: nomos-validate [--server URL] [--team NAME] schema <format> <compatibility_level>")
                return 1
            data = _post({"format": args[1], "compatibility_level": args[2]})
            label = f"{args[1]} / {args[2]}"
            return 0 if _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), label) else 1

        elif command == "rest-path":
            if len(args) < 2:
                print("Usage: nomos-validate [--server URL] [--team NAME] rest-path <path> [<path> ...]")
                return 1
            ok = True
            for path in args[1:]:
                data = _post({"path": path})
                if not _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), path):
                    ok = False
            return 0 if ok else 1

        elif command == "service-name":
            if len(args) < 2:
                print("Usage: nomos-validate [--server URL] [--team NAME] service-name <name> [<name> ...]")
                return 1
            ok = True
            for name in args[1:]:
                data = _post({"name": name})
                if not _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), name):
                    ok = False
            return 0 if ok else 1

    except httpx.ConnectError:
        print(f"ERR cannot connect to Nomos server at {server_url}")
        print(f"    Is the server running? Is the URL correct?")
        return 1
    except httpx.TimeoutException:
        print(f"ERR timeout connecting to {server_url}")
        return 1

    return 0


# ── Local mode ─────────────────────────────────────────────────────────────────

def _load_config():
    from src.loaders.local_loader import LocalLoader
    from src.config import settings
    return LocalLoader(settings.governance_repo_path).get_config()


def _local(team: str | None, args: list[str]) -> int:
    from src.validators import (
        topic as topic_validator,
        rbac as rbac_validator,
        sa_naming as sa_validator,
        schema as schema_validator,
        rest_path as rest_path_validator,
        service_name as service_name_validator,
    )

    if not args:
        print(__doc__)
        return 0

    config = _load_config()
    command = args[0]

    if command == "topic":
        if len(args) < 2:
            print("Usage: nomos-validate [--team NAME] topic <name> [<name> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, name)
            for name in args[1:]
            for r in [topic_validator.validate_topic_name(name, config.kafka.topic, team=team)]
        )
        return 0 if ok else 1

    if command == "rbac":
        if len(args) < 4:
            print("Usage: nomos-validate [--team NAME] rbac <role_name> <resource_type> <resource_name>")
            return 1
        r = rbac_validator.validate_rbac_binding(args[1], args[2], args[3], config.kafka.rbac, team=team)
        label = f"{args[1]} / {args[2]} / {args[3]}"
        return 0 if _print_result(r.valid, r.errors, r.warnings, label) else 1

    if command == "sa":
        if len(args) < 2:
            print("Usage: nomos-validate [--team NAME] sa <name> [<name> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, name)
            for name in args[1:]
            for r in [sa_validator.validate_sa_name(name, config.kafka.service_account, team=team)]
        )
        return 0 if ok else 1

    if command == "schema":
        if len(args) < 3:
            print("Usage: nomos-validate [--team NAME] schema <format> <compatibility_level>")
            return 1
        r = schema_validator.validate_schema_entry(args[1], args[2], config.kafka.schema_registry, team=team)
        label = f"{args[1]} / {args[2]}"
        return 0 if _print_result(r.valid, r.errors, r.warnings, label) else 1

    if command == "rest-path":
        if len(args) < 2:
            print("Usage: nomos-validate [--team NAME] rest-path <path> [<path> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, path)
            for path in args[1:]
            for r in [rest_path_validator.validate_rest_path(path, config.rest_api, team=team)]
        )
        return 0 if ok else 1

    if command == "service-name":
        if len(args) < 2:
            print("Usage: nomos-validate [--team NAME] service-name <name> [<name> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, name)
            for name in args[1:]
            for r in [service_name_validator.validate_service_name(name, config.service, team=team)]
        )
        return 0 if ok else 1

    print(f"Unknown command '{command}'. Available: topic, rbac, sa, schema, rest-path, service-name")
    return 1


# ── Entry point ────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    server_url, team, rest = _parse_flags(args)
    if server_url:
        return _remote(server_url, team, rest)
    return _local(team, rest)


if __name__ == "__main__":
    sys.exit(main())
