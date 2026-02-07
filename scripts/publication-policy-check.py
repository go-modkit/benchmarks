#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "results" / "latest" / "report.md"
REPORT_GENERATOR = ROOT / "scripts" / "generate-report.py"


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


def main() -> None:
    disclaimer_check()


if __name__ == "__main__":
    main()
