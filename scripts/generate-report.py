#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS_LATEST = ROOT / "results" / "latest"
RAW_DIR = RESULTS_LATEST / "raw"
SUMMARY_PATH = RESULTS_LATEST / "summary.json"
REPORT_PATH = RESULTS_LATEST / "report.md"


def load_raw_files():
    if not RAW_DIR.exists():
        return []
    rows = []
    for path in sorted(RAW_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                rows.append(json.load(f))
        except json.JSONDecodeError as exc:
            print(f"Warning: skipping malformed JSON {path}: {exc}")
    return rows


def build_summary(rows):
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
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
        }
        bench = row.get("benchmark") or {}
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
            "## Raw Artifacts",
            "",
            "- Raw JSON: `results/latest/raw/*.json`",
            "- Summary JSON: `results/latest/summary.json`",
        ]
    )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    rows = load_raw_files()
    summary = build_summary(rows)
    write_summary(summary)
    write_report(summary)
    print(f"Wrote: {SUMMARY_PATH}")
    print(f"Wrote: {REPORT_PATH}")


if __name__ == "__main__":
    main()
