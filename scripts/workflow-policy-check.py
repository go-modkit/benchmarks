#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Workflow file not found: {path}")
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, err: str) -> None:
    if needle not in text:
        raise SystemExit(err)


def check_concurrency() -> None:
    text = read_text(CI_WORKFLOW)
    assert_contains(
        text,
        "concurrency:\n  group: ci-${{ github.workflow }}-${{ github.ref }}\n  cancel-in-progress: true",
        "workflow-concurrency-check failed: top-level workflow concurrency with cancel-in-progress=true is required",
    )
    assert_contains(
        text,
        "  scripts:\n    name: Script smoke tests (skipped targets expected)\n    runs-on: ubuntu-latest\n    concurrency:\n      group: benchmark-smoke-${{ github.workflow }}-${{ github.ref }}\n      cancel-in-progress: true",
        "workflow-concurrency-check failed: scripts job must define benchmark concurrency with cancel-in-progress=true",
    )
    print("workflow-concurrency-check: validated workflow and benchmark job concurrency controls")


def check_budget() -> None:
    text = read_text(CI_WORKFLOW)
    assert_contains(
        text,
        "  scripts:\n    name: Script smoke tests (skipped targets expected)\n    runs-on: ubuntu-latest\n    timeout-minutes: 25",
        "workflow-budget-check failed: scripts job timeout-minutes budget must be set to 25",
    )
    assert_contains(
        text,
        "          retention-days: 14",
        "workflow-budget-check failed: benchmark-quality-summary artifact retention-days must be set",
    )
    print("workflow-budget-check: validated timeout budget and artifact retention policy")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate benchmark workflow safety policies")
    parser.add_argument("cmd", choices=["concurrency-check", "budget-check"])
    args = parser.parse_args()

    if args.cmd == "concurrency-check":
        check_concurrency()
    elif args.cmd == "budget-check":
        check_budget()


if __name__ == "__main__":
    main()
