#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS_LATEST = ROOT / "results" / "latest"
RAW_DIR = RESULTS_LATEST / "raw"
SUMMARY_PATH = RESULTS_LATEST / "summary.json"
REPORT_PATH = RESULTS_LATEST / "report.md"


def run_schema_check(command):
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "schema validation failed"
        raise SystemExit(message)


def load_raw_files():
    if not RAW_DIR.exists():
        return []
    rows = []
    for path in sorted(RAW_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
                payload["_source_file"] = path.name
                rows.append(payload)
        except json.JSONDecodeError as exc:
            print(f"Warning: skipping malformed JSON {path}: {exc}")
    return rows


def build_summary(rows):
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": "summary-v1",
        "generated_at": generated_at,
        "total_targets": len(rows),
        "successful_targets": sum(1 for r in rows if r.get("status") == "ok"),
        "skipped_targets": sum(1 for r in rows if r.get("status") != "ok"),
        "targets": [],
    }
    for row in rows:
        target = {
            "framework": row.get("framework"),
            "status": row.get("status"),
            "target": row.get("target"),
            "reason": row.get("reason"),
            "provenance": {
                "raw_source": f"results/latest/raw/{row.get('_source_file', 'unknown')}"
            },
        }
        bench = row.get("benchmark") or {}
        quality = (bench.get("quality") or {}).get("variance") or {}
        if quality:
            target["uncertainty"] = {
                "rps_cv": quality.get("rps_cv"),
                "latency_ms_p95_cv": quality.get("latency_ms_p95_cv"),
                "latency_ms_p99_cv": quality.get("latency_ms_p99_cv"),
            }
        median = bench.get("median") or {}
        if median:
            target["median"] = {
                "rps": median.get("rps"),
                "latency_ms_p50": median.get("latency_ms_p50"),
                "latency_ms_p95": median.get("latency_ms_p95"),
                "latency_ms_p99": median.get("latency_ms_p99"),
            }
        if row.get("resources_normalized"):
            target["resources_normalized"] = row.get("resources_normalized")
        if row.get("metric_units"):
            target["metric_units"] = row.get("metric_units")
        summary["targets"].append(target)
    return summary


def write_summary(summary):
    RESULTS_LATEST.mkdir(parents=True, exist_ok=True)
    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def write_report(summary):
    lines = [
        "# Benchmark Report",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Overview",
        f"- Total targets: {summary['total_targets']}",
        f"- Successful: {summary['successful_targets']}",
        f"- Skipped: {summary['skipped_targets']}",
        "",
        "## Results",
        "",
        "| Framework | Status | Median RPS | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for t in summary["targets"]:
        median = t.get("median") or {}
        rps = f"{median.get('rps', 0):.2f}" if "rps" in median else "-"
        p50 = f"{median.get('latency_ms_p50', 0):.2f}" if "latency_ms_p50" in median else "-"
        p95 = f"{median.get('latency_ms_p95', 0):.2f}" if "latency_ms_p95" in median else "-"
        p99 = f"{median.get('latency_ms_p99', 0):.2f}" if "latency_ms_p99" in median else "-"
        notes = t.get("reason") or ""
        lines.append(f"| {t.get('framework','-')} | {t.get('status','-')} | {rps} | {p50} | {p95} | {p99} | {notes} |")

    lines.extend(
        [
            "",
            "## Fairness Disclaimer",
            "",
            "- Language-vs-framework caveat: cross-language results include runtime and ecosystem effects and must not be treated as framework-only deltas.",
            "- Cross-language baseline: compare implementations with equivalent API behavior, workload profile, and environment constraints before drawing conclusions.",
            "",
            "## Anti-Misinterpretation Guidance",
            "",
            "- Do not rank frameworks across languages as absolute winners; use results as scenario-specific signals.",
            "- Treat large cross-language deltas as prompts for deeper profiling (runtime, I/O, GC, and dependency effects), not as standalone product claims.",
            "- Parity failures invalidate performance interpretation until correctness is restored.",
            "",
            "## Raw Artifacts",
            "",
            "- Raw JSON: `results/latest/raw/*.json`",
            "- Summary JSON: `results/latest/summary.json`",
        ]
    )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    run_schema_check([sys.executable, "scripts/validate-result-schemas.py", "raw-check"])
    rows = load_raw_files()
    summary = build_summary(rows)
    write_summary(summary)
    run_schema_check([sys.executable, "scripts/validate-result-schemas.py", "summary-check"])
    write_report(summary)
    print(f"Wrote: {SUMMARY_PATH}")
    print(f"Wrote: {REPORT_PATH}")


if __name__ == "__main__":
    main()
