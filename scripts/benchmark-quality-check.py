#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "results" / "latest" / "raw"


def load_raw_rows(raw_dir):
    if not raw_dir.exists():
        raise SystemExit(f"Raw results directory not found: {raw_dir}")

    rows = []
    for path in sorted(raw_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            rows.append((path, json.load(handle)))

    if not rows:
        raise SystemExit(f"No raw benchmark files found in: {raw_dir}")
    return rows


def ensure_number(value, label):
    if isinstance(value, (int, float)):
        return
    raise SystemExit(f"Invalid or missing numeric field: {label}")


def check_stats(args):
    rows = load_raw_rows(args.raw_dir)
    checked = 0

    for path, row in rows:
        if row.get("status") != "ok":
            continue

        checked += 1
        median = ((row.get("benchmark") or {}).get("median") or {})
        ensure_number(median.get("rps"), f"{path}: benchmark.median.rps")
        ensure_number(median.get("latency_ms_p50"), f"{path}: benchmark.median.latency_ms_p50")
        ensure_number(median.get("latency_ms_p95"), f"{path}: benchmark.median.latency_ms_p95")
        ensure_number(median.get("latency_ms_p99"), f"{path}: benchmark.median.latency_ms_p99")

        units = row.get("metric_units") or {}
        expected_units = {
            "throughput": "requests_per_second",
            "latency": "milliseconds",
            "memory": "mb",
            "cpu": "percent",
            "startup": "milliseconds",
        }
        for key, expected in expected_units.items():
            value = units.get(key)
            if value != expected:
                raise SystemExit(
                    f"Unexpected unit for {path}: metric_units.{key}={value!r}, expected {expected!r}"
                )

        resources = row.get("resources_normalized") or {}
        for key in ("memory_mb", "cpu_percent", "startup_ms"):
            value = resources.get(key)
            if value is not None and not isinstance(value, (int, float)):
                raise SystemExit(
                    f"Invalid normalized resource field in {path}: resources_normalized.{key}"
                )

    if checked == 0:
        print("benchmark-stats-check: no successful targets to validate (all skipped)")
        return

    print(f"benchmark-stats-check: validated {checked} successful target(s)")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark quality checks")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory with per-framework raw benchmark JSON files",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats-check", help="Validate aggregate benchmark statistic fields")

    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == "stats-check":
        check_stats(args)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
