#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "results" / "latest" / "raw"
QUALITY_SUMMARY_FILE = REPO_ROOT / "results" / "latest" / "benchmark-quality-summary.json"
POLICY_FILE = REPO_ROOT / "stats-policy.yaml"
TOOLING_DIR = REPO_ROOT / "results" / "latest" / "tooling"


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


def load_policy(path):
    if not path.exists():
        raise SystemExit(f"Policy file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def ensure_number(value, label):
    if isinstance(value, (int, float)):
        return float(value)
    raise SystemExit(f"Invalid or missing numeric field: {label}")


def get_path_value(data, dotted_path):
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def check_stats(args, policy):
    rows = load_raw_rows(args.raw_dir)
    checked = 0
    quality_policy = policy.get("quality") or {}
    required_metrics = quality_policy.get("required_metrics") or []
    expected_units = quality_policy.get("metric_units") or {}

    for path, row in rows:
        if row.get("status") != "ok":
            continue

        checked += 1
        for metric_path in required_metrics:
            ensure_number(get_path_value(row, metric_path), f"{path}: {metric_path}")

        units = row.get("metric_units") or {}
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


def check_variance(args, policy):
    rows = load_raw_rows(args.raw_dir)
    quality_policy = policy.get("quality") or {}
    thresholds = quality_policy.get("variance_thresholds_cv") or {}

    summary = {
        "status": "passed",
        "mode": "policy+variance",
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
            threshold_num = ensure_number(threshold, f"policy.quality.variance_thresholds_cv.{threshold_key}")
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
        return summary

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
    return summary


def write_benchstat_input(path, framework, run_stats):
    lines = []
    for index, run in enumerate(run_stats, start=1):
        rps = ensure_number(run.get("rps"), f"{framework}: benchmark.run_stats[{index}].rps")
        ns_per_op = 1_000_000_000.0 / rps
        lines.append(f"Benchmark{framework}-8 {index} {ns_per_op:.0f} ns/op")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_delta_percent(output):
    percent_matches = re.findall(r"([+-]?[0-9]+(?:\.[0-9]+)?)%", output)
    if not percent_matches:
        return None
    return float(percent_matches[-1])


def check_benchstat(args, policy):
    quality_policy = policy.get("quality") or {}
    benchstat_policy = quality_policy.get("benchstat") or {}
    if not benchstat_policy.get("enabled", False):
        print("benchmark-benchstat-check: disabled by policy")
        return {"status": "skipped", "reason": "disabled"}

    benchstat_bin = shutil.which("benchstat")
    if benchstat_bin is None:
        gopath = subprocess.run(
            ["go", "env", "GOPATH"],
            capture_output=True,
            text=True,
            check=False,
        )
        if gopath.returncode == 0:
            candidate = Path(gopath.stdout.strip()) / "bin" / "benchstat"
            if candidate.exists():
                benchstat_bin = str(candidate)
    if benchstat_bin is None:
        raise SystemExit("benchmark-benchstat-check: benchstat not found in PATH")

    rows = load_raw_rows(args.raw_dir)
    by_framework = {
        (row.get("framework") or path.stem): row
        for path, row in rows
        if row.get("status") == "ok"
    }

    baseline_framework = benchstat_policy.get("baseline_framework", "baseline")
    baseline = by_framework.get(baseline_framework)
    if baseline is None:
        print("benchmark-benchstat-check: baseline framework not present in successful targets")
        return {"status": "skipped", "reason": "baseline_missing"}

    max_regression = ensure_number(
        ((benchstat_policy.get("max_regression_percent") or {}).get("ns_per_op")),
        "policy.quality.benchstat.max_regression_percent.ns_per_op",
    )

    TOOLING_DIR.mkdir(parents=True, exist_ok=True)
    benchstat_dir = TOOLING_DIR / "benchstat"
    benchstat_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "passed",
        "baseline_framework": baseline_framework,
        "max_regression_percent": max_regression,
        "comparisons": [],
        "failures": [],
    }

    with tempfile.TemporaryDirectory(prefix="benchstat-", dir=benchstat_dir) as temp_dir:
        temp_root = Path(temp_dir)
        baseline_file = temp_root / f"{baseline_framework}.txt"
        write_benchstat_input(
            baseline_file,
            baseline_framework,
            ((baseline.get("benchmark") or {}).get("run_stats") or []),
        )

        for framework, row in sorted(by_framework.items()):
            if framework == baseline_framework:
                continue

            current_file = temp_root / f"{framework}.txt"
            write_benchstat_input(
                current_file,
                framework,
                ((row.get("benchmark") or {}).get("run_stats") or []),
            )

            completed = subprocess.run(
                [benchstat_bin, str(baseline_file), str(current_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                raise SystemExit(f"benchstat failed for {framework}: {completed.stderr.strip()}")

            output_text = completed.stdout.strip() + "\n"
            out_file = benchstat_dir / f"{framework}.txt"
            out_file.write_text(output_text, encoding="utf-8")

            delta = parse_delta_percent(output_text)
            comparison = {
                "framework": framework,
                "baseline": baseline_framework,
                "delta_percent_ns_per_op": delta,
                "output_file": str(out_file.relative_to(REPO_ROOT)),
                "status": "passed",
            }
            if delta is None:
                comparison["status"] = "failed"
                comparison["reason"] = "delta_parse_failed"
                summary["failures"].append(f"{framework}: unable to parse benchstat delta")
            elif delta > max_regression:
                comparison["status"] = "failed"
                comparison["reason"] = (
                    f"delta {delta:.2f}% exceeded max regression {max_regression:.2f}%"
                )
                summary["failures"].append(
                    f"{framework}: ns/op regression {delta:.2f}% > {max_regression:.2f}%"
                )

            summary["comparisons"].append(comparison)

    if summary["failures"]:
        summary["status"] = "failed"
        raise SystemExit("benchmark-benchstat-check failed: " + summary["failures"][0])

    print(
        "benchmark-benchstat-check: "
        f"validated {len(summary['comparisons'])} framework comparison(s) against {baseline_framework}"
    )
    return summary


def run_ci_check(args, policy):
    check_stats(args, policy)
    variance_summary = check_variance(args, policy)
    benchstat_summary = check_benchstat(args, policy)
    ci_summary = {
        "status": "passed",
        "policy_file": str(args.policy_file),
        "checks": {
            "variance": variance_summary,
            "benchstat": benchstat_summary,
        },
    }
    if (
        variance_summary.get("status") == "failed"
        or benchstat_summary.get("status") == "failed"
    ):
        ci_summary["status"] = "failed"
    args.summary_file.parent.mkdir(parents=True, exist_ok=True)
    args.summary_file.write_text(json.dumps(ci_summary, indent=2) + "\n", encoding="utf-8")
    print(f"ci-benchmark-quality-check: wrote summary {args.summary_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark quality checks")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--summary-file", type=Path, default=QUALITY_SUMMARY_FILE)
    parser.add_argument("--policy-file", type=Path, default=POLICY_FILE)

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats-check")
    sub.add_parser("variance-check")
    sub.add_parser("benchstat-check")
    sub.add_parser("ci-check")

    return parser.parse_args()


def main():
    args = parse_args()
    policy = load_policy(args.policy_file)

    if args.cmd == "stats-check":
        check_stats(args, policy)
        return
    if args.cmd == "variance-check":
        check_variance(args, policy)
        return
    if args.cmd == "benchstat-check":
        check_benchstat(args, policy)
        return
    if args.cmd == "ci-check":
        run_ci_check(args, policy)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
