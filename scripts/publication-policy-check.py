#!/usr/bin/env python3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "results" / "latest" / "report.md"
REPORT_GENERATOR = ROOT / "scripts" / "generate-report.py"
METHODOLOGY = ROOT / "METHODOLOGY.md"


def report_content() -> str:
    if REPORT.exists():
        return REPORT.read_text(encoding="utf-8")
    return ""


def generator_template_content() -> str:
    if not REPORT_GENERATOR.exists():
        raise SystemExit(f"report-disclaimer-check failed: missing generator at {REPORT_GENERATOR}")
    return REPORT_GENERATOR.read_text(encoding="utf-8")


def disclaimer_check() -> None:
    content = report_content()
    template = generator_template_content()
    required = [
        "## Fairness Disclaimer",
        "Language-vs-framework caveat",
        "## Anti-Misinterpretation Guidance",
        "cross-language",
    ]
    for token in required:
        if token not in template:
            raise SystemExit(f"report-disclaimer-check failed: missing '{token}' in scripts/generate-report.py")
        if REPORT.exists() and token not in content:
            raise SystemExit(f"report-disclaimer-check failed: missing '{token}' in results/latest/report.md")
    source = "report + generator" if REPORT.exists() else "generator template"
    print(f"report-disclaimer-check: validated disclaimer sections via {source}")


def changelog_check() -> None:
    if not METHODOLOGY.exists():
        raise SystemExit(f"methodology-changelog-check failed: missing {METHODOLOGY}")

    content = METHODOLOGY.read_text(encoding="utf-8")
    required = [
        "## Methodology changelog policy",
        "### Update rules",
        "### Entry format",
        "### Changelog",
        "comparability-impacting",
        "| version | date (UTC) | change_type | summary | comparability_impact | required_action |",
    ]
    for token in required:
        if token not in content:
            raise SystemExit(f"methodology-changelog-check failed: missing '{token}' in METHODOLOGY.md")

    changelog_rows = [
        line
        for line in content.splitlines()
        if line.startswith("|") and "comparability-impacting" in line
    ]
    if not changelog_rows:
        raise SystemExit(
            "methodology-changelog-check failed: changelog requires at least one comparability-impacting entry"
        )
    print("methodology-changelog-check: validated changelog policy and comparability entries")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "report-disclaimer-check"
    if command == "report-disclaimer-check":
        disclaimer_check()
        return
    if command == "methodology-changelog-check":
        changelog_check()
        return
    raise SystemExit(
        "usage: publication-policy-check.py [report-disclaimer-check|methodology-changelog-check]"
    )


if __name__ == "__main__":
    main()
