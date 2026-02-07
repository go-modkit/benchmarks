#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "results" / "latest" / "raw"
QUALITY_SUMMARY_FILE = REPO_ROOT / "results" / "latest" / "benchmark-quality-summary.json"


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
        return float(value)
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


def check_variance(args):
    rows = load_raw_rows(args.raw_dir)
    summary = {
        "status": "passed",
        "targets_checked": 0,
        "targets_failed": 0,
        "failures": [],
        "targets": [],
    }

    for path, row in rows:
        if row.get("status") != "ok":
            continue

        quality = ((row.get("benchmark") or {}).get("quality") or {})
        variance = quality.get("variance") or {}
        policy = quality.get("policy") or {}
        thresholds = policy.get("variance_thresholds_cv") or {}
        excluded_samples = quality.get("excluded_samples") or []

        framework = row.get("framework") or path.stem
        target_result = {
            "framework": framework,
            "source_file": path.name,
            "excluded_samples": excluded_samples,
            "variance": {
                "rps_cv": variance.get("rps_cv"),
                "latency_ms_p95_cv": variance.get("latency_ms_p95_cv"),
                "latency_ms_p99_cv": variance.get("latency_ms_p99_cv"),
            },
            "thresholds": {
                "rps": thresholds.get("rps"),
                "latency_ms_p95": thresholds.get("latency_ms_p95"),
                "latency_ms_p99": thresholds.get("latency_ms_p99"),
            },
            "status": "passed",
            "violations": [],
        }

        checks = [
            ("rps_cv", "rps"),
            ("latency_ms_p95_cv", "latency_ms_p95"),
            ("latency_ms_p99_cv", "latency_ms_p99"),
        ]

        for variance_key, threshold_key in checks:
            value = variance.get(variance_key)
            threshold = thresholds.get(threshold_key)
            value_num = ensure_number(value, f"{path}: benchmark.quality.variance.{variance_key}")
            threshold_num = ensure_number(
                threshold,
                f"{path}: benchmark.quality.policy.variance_thresholds_cv.{threshold_key}",
            )
            if value_num > threshold_num:
                target_result["violations"].append(
                    {
                        "metric": variance_key,
                        "value": value_num,
                        "threshold": threshold_num,
                        "message": (
                            f"{framework}: {variance_key}={value_num:.4f} exceeded threshold={threshold_num:.4f} "
                            f"after excluding {len(excluded_samples)} outlier sample(s)"
                        ),
                    }
                )

        summary["targets_checked"] += 1
        if target_result["violations"]:
            target_result["status"] = "failed"
            summary["targets_failed"] += 1
            summary["failures"].extend(target_result["violations"])

        summary["targets"].append(target_result)

    if summary["targets_failed"] > 0:
        summary["status"] = "failed"

    args.summary_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["targets_checked"] == 0:
        print("benchmark-variance-check: no successful targets to validate (all skipped)")
        print(f"benchmark-variance-check: wrote summary {args.summary_file}")
        return

    if summary["status"] == "failed":
        first = summary["failures"][0]["message"]
        print(f"benchmark-variance-check: wrote summary {args.summary_file}")
        raise SystemExit(f"benchmark-variance-check failed: {first}")

    print(
        "benchmark-variance-check: "
        f"validated {summary['targets_checked']} successful target(s); "
        f"excluded sample records={sum(len(t['excluded_samples']) for t in summary['targets'])}"
    )
    print(f"benchmark-variance-check: wrote summary {args.summary_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark quality checks")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory with per-framework raw benchmark JSON files",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=QUALITY_SUMMARY_FILE,
        help="Output JSON summary file for quality checks",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats-check", help="Validate aggregate benchmark statistic fields")
    sub.add_parser("variance-check", help="Validate variance policy and outlier recording")

    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == "stats-check":
        check_stats(args)
        return
    if args.cmd == "variance-check":
        check_variance(args)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
