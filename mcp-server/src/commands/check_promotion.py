"""
nomos check-promotion — verify a @wip Gherkin scenario is ready to promote to @enforced.

Checks:
  1. All steps in the feature file have matching step definitions (behave --dry-run)
  2. Optionally runs the full scenario suite (--run)

Usage:
    nomos check-promotion features/kafka/topic-naming.feature
    nomos check-promotion features/kafka/topic-naming.feature --run
    nomos check-promotion features/kafka/topic-naming.feature --repo /path/to/governance-repo
"""
import os
import subprocess
import sys
from pathlib import Path


def run(args) -> int:
    feature_path = Path(args.feature_file)
    if not feature_path.exists():
        print(f"ERR  feature file not found: {feature_path}")
        return 1

    content = feature_path.read_text()
    if "@enforced" in content and "@wip" not in content:
        print(f"WARN {feature_path} appears to already be @enforced")

    repo_path = Path(
        args.repo if args.repo else os.environ.get("GOVERNANCE_REPO_PATH", ".")
    ).resolve()

    print(f"Feature file:    {feature_path}")
    print(f"Governance repo: {repo_path}")
    print()

    env = {**os.environ, "GOVERNANCE_REPO_PATH": str(repo_path)}

    # Step 1 — dry run: checks step definitions exist without executing them
    print("Step 1/2: checking step definitions...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "behave", str(feature_path), "--dry-run", "--no-skipped"],
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        print("ERR  behave not found — install with: pip install behave")
        return 1

    if result.returncode != 0:
        print("ERR  missing step definitions:")
        print()
        # behave dry-run output goes to stdout
        for line in result.stdout.splitlines():
            print(f"     {line}")
        if result.stderr.strip():
            for line in result.stderr.splitlines():
                print(f"     {line}")
        print()
        print("Add step definitions in features/steps/ then retry.")
        print("See features/steps/README.md for guidance.")
        return 1

    print("OK   all step definitions found")

    # Step 2 — full run (optional)
    if args.run:
        print()
        print("Step 2/2: running full scenario suite...")
        result = subprocess.run(
            [sys.executable, "-m", "behave", str(feature_path), "--no-skipped"],
            env=env,
        )
        if result.returncode != 0:
            print()
            print("ERR  one or more scenarios failed — fix before promoting")
            return 1
        print()
        print("OK   all scenarios pass")
    else:
        print()
        print("Tip: run with --run to execute the full scenario suite before promoting")

    print()
    print("Ready to promote:")
    print(f"  1. Change @wip to @enforced in {feature_path}")
    print(f"  2. Open a promotion PR with the behave output")
    print(f"  3. Domain owner approves — no additional reviewers required")
    return 0


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "check-promotion",
        help="Verify a @wip Gherkin scenario is ready to be promoted to @enforced",
    )
    p.add_argument(
        "feature_file",
        metavar="FEATURE_FILE",
        help="Path to the .feature file to check",
    )
    p.add_argument(
        "--run",
        action="store_true",
        help="Also execute the full scenario suite (not just check definitions)",
    )
    p.add_argument(
        "--repo",
        metavar="PATH",
        help="Governance repo path (default: GOVERNANCE_REPO_PATH env var, or .)",
    )
    p.set_defaults(func=run)
