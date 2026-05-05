"""
govern-mcp validator CLI — usable as pre-commit hook or in CI pipelines.

Usage:
    python -m src topic "raw.sales.pos.hmsu.commons.guestcheck.v1"
    python -m src rbac DeveloperRead topic "raw.sales.*"
    python -m src sa "sa-sales-lsretail-lookup-connector-source-jdbc-dev"

Reads governance.yml from the repo root (GOVERNANCE_REPO_PATH in .env).
Exit code: 0 if valid, 1 if any errors.
"""
import sys
from pathlib import Path
from src.validators import topic as topic_validator, rbac as rbac_validator, sa_naming as sa_validator


def _load_config():
    from src.loaders.local_loader import LocalLoader
    from src.config import settings
    loader = LocalLoader(settings.governance_repo_path)
    return loader.get_config()


def _print_result(result, label: str) -> bool:
    if result.valid:
        print(f"OK  {label}")
        for w in result.warnings:
            print(f"    WARNING: {w}")
    else:
        print(f"ERR {label}")
        for e in result.errors:
            print(f"    {e}")
    return result.valid


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    if not args:
        print(__doc__)
        return 0

    config = _load_config()
    command = args[0]

    if command == "topic":
        if len(args) < 2:
            print("Usage: python -m src topic <topic-name> [<topic-name> ...]")
            return 1
        ok = all(
            _print_result(topic_validator.validate_topic_name(name, config.kafka.topic), name)
            for name in args[1:]
        )
        return 0 if ok else 1

    if command == "rbac":
        if len(args) < 4:
            print("Usage: python -m src rbac <role_name> <resource_type> <resource_name>")
            return 1
        result = rbac_validator.validate_rbac_binding(args[1], args[2], args[3], config.kafka.rbac)
        label = f"{args[1]} / {args[2]} / {args[3]}"
        return 0 if _print_result(result, label) else 1

    if command == "sa":
        if len(args) < 2:
            print("Usage: python -m src sa <sa-name> [<sa-name> ...]")
            return 1
        ok = all(
            _print_result(sa_validator.validate_sa_name(name, config.kafka.service_account), name)
            for name in args[1:]
        )
        return 0 if ok else 1

    print(f"Unknown command '{command}'. Available: topic, rbac, sa")
    return 1


if __name__ == "__main__":
    sys.exit(main())
