"""
nomos-validate — CLI validator, usable as pre-commit hook or in CI pipelines.

Local mode (reads governance.yml from GOVERNANCE_REPO_PATH):
    nomos-validate topic "acme.payments.checkout.team.receipts.transaction.v1"
    nomos-validate rbac DeveloperRead topic "acme.payments.*"
    nomos-validate sa "sa-payments-connector-source-jdbc-prod"

Remote mode (delegates to a shared Nomos server):
    nomos-validate --server https://governance.acme.com topic "acme.payments..."
    nomos-validate --server https://governance.acme.com rbac DeveloperRead topic "acme.*"
    nomos-validate --server https://governance.acme.com sa "sa-payments-..."

Exit code: 0 if valid, 1 if any errors.
"""
import sys
from pathlib import Path


def _parse_server_flag(argv: list[str]) -> tuple[str | None, list[str]]:
    server_url = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--server" and i + 1 < len(argv):
            server_url = argv[i + 1].rstrip("/")
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    return server_url, rest


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

def _remote(server_url: str, args: list[str]) -> int:
    import httpx

    if not args:
        print(__doc__)
        return 0

    command = args[0]
    endpoint_map = {"topic": "/validate/topic", "rbac": "/validate/rbac", "sa": "/validate/sa"}

    if command not in endpoint_map:
        print(f"Unknown command '{command}'. Available: topic, rbac, sa")
        return 1

    url = server_url + endpoint_map[command]

    try:
        if command == "topic":
            if len(args) < 2:
                print("Usage: nomos-validate --server URL topic <name> [<name> ...]")
                return 1
            ok = True
            for name in args[1:]:
                r = httpx.post(url, json={"name": name}, timeout=10)
                data = r.json()
                if not _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), name):
                    ok = False
            return 0 if ok else 1

        elif command == "rbac":
            if len(args) < 4:
                print("Usage: nomos-validate --server URL rbac <role_name> <resource_type> <resource_name>")
                return 1
            r = httpx.post(url, json={"role_name": args[1], "resource_type": args[2], "resource_name": args[3]}, timeout=10)
            data = r.json()
            label = f"{args[1]} / {args[2]} / {args[3]}"
            ok = _print_result(data.get("valid", False), data.get("errors", []), data.get("warnings", []), label)
            return 0 if ok else 1

        elif command == "sa":
            if len(args) < 2:
                print("Usage: nomos-validate --server URL sa <name> [<name> ...]")
                return 1
            ok = True
            for name in args[1:]:
                r = httpx.post(url, json={"name": name}, timeout=10)
                data = r.json()
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


def _local(args: list[str]) -> int:
    from src.validators import topic as topic_validator, rbac as rbac_validator, sa_naming as sa_validator

    if not args:
        print(__doc__)
        return 0

    config = _load_config()
    command = args[0]

    if command == "topic":
        if len(args) < 2:
            print("Usage: nomos-validate topic <name> [<name> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, name)
            for name in args[1:]
            for r in [topic_validator.validate_topic_name(name, config.kafka.topic)]
        )
        return 0 if ok else 1

    if command == "rbac":
        if len(args) < 4:
            print("Usage: nomos-validate rbac <role_name> <resource_type> <resource_name>")
            return 1
        r = rbac_validator.validate_rbac_binding(args[1], args[2], args[3], config.kafka.rbac)
        label = f"{args[1]} / {args[2]} / {args[3]}"
        return 0 if _print_result(r.valid, r.errors, r.warnings, label) else 1

    if command == "sa":
        if len(args) < 2:
            print("Usage: nomos-validate sa <name> [<name> ...]")
            return 1
        ok = all(
            _print_result(r.valid, r.errors, r.warnings, name)
            for name in args[1:]
            for r in [sa_validator.validate_sa_name(name, config.kafka.service_account)]
        )
        return 0 if ok else 1

    print(f"Unknown command '{command}'. Available: topic, rbac, sa")
    return 1


# ── Entry point ────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    server_url, rest = _parse_server_flag(args)
    if server_url:
        return _remote(server_url, rest)
    return _local(rest)


if __name__ == "__main__":
    sys.exit(main())
