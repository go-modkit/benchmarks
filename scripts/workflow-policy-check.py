#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
MANUAL_WORKFLOW = ROOT / ".github" / "workflows" / "benchmark-manual.yml"


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
        "  scripts:\n    name: Script smoke tests (skipped targets expected)",
        "workflow-concurrency-check failed: scripts benchmark smoke job is missing",
    )
    assert_contains(
        text,
        "      group: benchmark-smoke-${{ github.workflow }}-${{ github.ref }}",
        "workflow-concurrency-check failed: scripts job benchmark concurrency group is missing",
    )
    assert_contains(
        text,
        "      cancel-in-progress: true",
        "workflow-concurrency-check failed: scripts job cancel-in-progress=true is required",
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


def check_inputs() -> None:
    text = read_text(MANUAL_WORKFLOW)
    assert_contains(
        text,
        "workflow_dispatch:",
        "workflow-inputs-check failed: benchmark-manual workflow_dispatch is required",
    )
    for key in ("frameworks", "runs", "benchmark_requests"):
        assert_contains(
            text,
            f"      {key}:",
            f"workflow-inputs-check failed: missing workflow_dispatch input '{key}'",
        )
    for token in (
        "INPUT_FRAMEWORKS",
        "INPUT_RUNS",
        "INPUT_BENCHMARK_REQUESTS",
        "BENCH_RUNS",
        "BENCH_REQUESTS",
        "runs must be between 1 and 10",
        "benchmark_requests must be between 50 and 1000",
    ):
        assert_contains(
            text,
            token,
            f"workflow-inputs-check failed: missing bounded input token '{token}'",
        )
    print("workflow-inputs-check: validated bounded manual workflow inputs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate benchmark workflow safety policies")
    parser.add_argument("cmd", choices=["concurrency-check", "budget-check", "inputs-check"])
    args = parser.parse_args()

    if args.cmd == "concurrency-check":
        check_concurrency()
    elif args.cmd == "budget-check":
        check_budget()
    elif args.cmd == "inputs-check":
        check_inputs()


if __name__ == "__main__":
    main()
