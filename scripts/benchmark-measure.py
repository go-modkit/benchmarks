#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from benchlib.io_utils import load_json_policy


UNIT_TO_MB = {
    "b": 1 / (1024 * 1024),
    "kb": 1 / 1000,
    "kib": 1 / 1024,
    "mb": 1,
    "mib": 1,
    "gb": 1000,
    "gib": 1024,
    "tb": 1000 * 1000,
    "tib": 1024 * 1024,
}


def parse_mem_to_mb(value):
    if not value:
        return None
    head = str(value).split("/", 1)[0].strip()
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)$", head)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2).lower()
    factor = UNIT_TO_MB.get(unit)
    if factor is None:
        return None
    return amount * factor


def parse_cpu_percent(value):
    if not value:
        return None
    raw = str(value).strip().removesuffix("%")
    try:
        return float(raw)
    except ValueError:
        return None


def coefficient_of_variation(values):
    if len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    if mean == 0:
        return 0.0
    return statistics.stdev(values) / mean


def detect_iqr_outlier_indexes(values):
    if len(values) < 4:
        return set(), None, None
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    if iqr <= 0:
        return set(), q1, q3
    lower = q1 - (1.5 * iqr)
    upper = q3 + (1.5 * iqr)
    indexes = {idx for idx, value in enumerate(values) if value < lower or value > upper}
    return indexes, lower, upper


def request_once(url):
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=5) as response:
        response.read()
    return time.perf_counter() - start


def measure_legacy(url, warmup, requests, runs):
    warmup_first_success = None
    for _ in range(warmup):
        try:
            duration = request_once(url)
            if warmup_first_success is None:
                warmup_first_success = duration
        except Exception:
            continue

    run_stats = []
    for _ in range(runs):
        durations = []
        for _ in range(requests):
            try:
                durations.append(request_once(url))
            except Exception:
                continue
        if not durations:
            continue
        total = sum(durations)
        run_stats.append(
            {
                "requests": requests,
                "duration_seconds": total,
                "rps": requests / total if total > 0 else 0.0,
                "latency_ms_p50": statistics.median(durations) * 1000,
                "latency_ms_p95": statistics.quantiles(durations, n=20)[18] * 1000,
                "latency_ms_p99": statistics.quantiles(durations, n=100)[98] * 1000,
                "latency_ms_max": max(durations) * 1000,
            }
        )

    return run_stats, warmup_first_success


def measure_hyperfine(repo_root, url, requests, runs):
    if shutil.which("hyperfine") is None:
        raise SystemExit("BENCH_ENGINE=hyperfine requires hyperfine installed")

    with tempfile.TemporaryDirectory(prefix="hyperfine-", dir=repo_root / "results" / "latest") as temp_dir:
        export_file = Path(temp_dir) / "hyperfine.json"
        batch_command = (
            f"python3 scripts/http-batch.py --url {shlex.quote(url)} "
            f"--requests {int(requests)} --timeout 5"
        )
        completed = subprocess.run(
            [
                "hyperfine",
                "--shell",
                "sh",
                "--runs",
                str(runs),
                "--warmup",
                "1",
                "--export-json",
                str(export_file),
                batch_command,
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"hyperfine failed: {completed.stderr.strip() or completed.stdout.strip()}")

        payload = json.loads(export_file.read_text(encoding="utf-8"))
        results = payload.get("results") or []
        if not results:
            raise SystemExit("hyperfine produced no results")

        times = results[0].get("times") or []
        if not times:
            raise SystemExit("hyperfine produced no timing samples")

    run_stats = []
    for duration in times:
        run_seconds = float(duration)
        if run_seconds <= 0:
            continue
        latency_ms = (run_seconds * 1000) / requests
        run_stats.append(
            {
                "requests": requests,
                "duration_seconds": run_seconds,
                "rps": requests / run_seconds,
                "latency_ms_p50": latency_ms,
                "latency_ms_p95": latency_ms,
                "latency_ms_p99": latency_ms,
                "latency_ms_max": latency_ms,
            }
        )

    return run_stats, None


def load_policy(repo_root):
    policy_file = repo_root / "stats-policy.json"
    if not policy_file.exists():
        policy_file = repo_root / "stats-policy.yaml"
    return load_json_policy(policy_file, default_on_missing={})


def collect_docker_stats(framework):
    docker_stats = {}
    try:
        completed = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.MemUsage}}|{{.CPUPerc}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3 and (
                parts[0] == framework
                or parts[0].startswith(framework + "-")
                or parts[0].endswith("-" + framework)
            ):
                docker_stats = {"container": parts[0], "memory": parts[1], "cpu": parts[2]}
                break
    except Exception:
        pass
    return docker_stats


def main():
    parser = argparse.ArgumentParser(description="Collect benchmark metrics for one framework")
    parser.add_argument("--framework", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--warmup-requests", required=True, type=int)
    parser.add_argument("--benchmark-requests", required=True, type=int)
    parser.add_argument("--runs", required=True, type=int)
    parser.add_argument("--out-file", required=True, type=Path)
    parser.add_argument("--parity-result", required=True)
    parser.add_argument("--engine", default=os.environ.get("BENCH_ENGINE", "legacy"))
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    policy = load_policy(repo_root)
    quality_policy = (policy.get("quality") or {})
    variance_thresholds = quality_policy.get("variance_thresholds_cv") or {
        "rps": 0.10,
        "latency_ms_p95": 0.20,
        "latency_ms_p99": 0.25,
    }

    url = args.target.rstrip("/") + args.endpoint
    if args.engine == "hyperfine":
        run_stats, warmup_first_success = measure_hyperfine(repo_root, url, args.benchmark_requests, args.runs)
    else:
        run_stats, warmup_first_success = measure_legacy(url, args.warmup_requests, args.benchmark_requests, args.runs)

    if not run_stats:
        payload = {
            "schema_version": "raw-v1",
            "framework": args.framework,
            "target": args.target,
            "status": "skipped",
            "reason": "benchmark requests failed",
            "parity": args.parity_result,
            "engine": args.engine,
        }
        args.out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"SKIP {args.framework}: benchmark requests failed")
        return

    rps_values = [r["rps"] for r in run_stats]
    p95_values = [r["latency_ms_p95"] for r in run_stats]
    rps_outliers, rps_lower, rps_upper = detect_iqr_outlier_indexes(rps_values)
    p95_outliers, p95_lower, p95_upper = detect_iqr_outlier_indexes(p95_values)
    excluded_indexes = sorted(rps_outliers | p95_outliers)

    excluded_samples = []
    for idx in excluded_indexes:
        reasons = []
        if idx in rps_outliers:
            reasons.append("rps_outlier")
        if idx in p95_outliers:
            reasons.append("latency_p95_outlier")
        excluded_samples.append({"run_index": idx, "reasons": reasons, "run": run_stats[idx]})

    filtered_run_stats = [r for idx, r in enumerate(run_stats) if idx not in excluded_indexes]
    if not filtered_run_stats:
        filtered_run_stats = run_stats

    filtered_rps = [r["rps"] for r in filtered_run_stats]
    filtered_p50 = [r["latency_ms_p50"] for r in filtered_run_stats]
    filtered_p95 = [r["latency_ms_p95"] for r in filtered_run_stats]
    filtered_p99 = [r["latency_ms_p99"] for r in filtered_run_stats]

    docker_stats = collect_docker_stats(args.framework)

    payload = {
        "schema_version": "raw-v1",
        "framework": args.framework,
        "target": args.target,
        "status": "ok",
        "parity": args.parity_result,
        "engine": args.engine,
        "metric_units": {
            "throughput": "requests_per_second",
            "latency": "milliseconds",
            "memory": "mb",
            "cpu": "percent",
            "startup": "milliseconds",
        },
        "benchmark": {
            "endpoint": args.endpoint,
            "warmup_requests": args.warmup_requests,
            "requests_per_run": args.benchmark_requests,
            "runs": args.runs,
            "run_stats": run_stats,
            "quality": {
                "policy": {
                    "outlier_method": "iqr_1.5",
                    "outlier_thresholds": {
                        "rps": {"lower": rps_lower, "upper": rps_upper},
                        "latency_ms_p95": {"lower": p95_lower, "upper": p95_upper},
                    },
                    "variance_thresholds_cv": variance_thresholds,
                },
                "excluded_samples": excluded_samples,
                "effective_runs": len(filtered_run_stats),
                "variance": {
                    "rps_cv": coefficient_of_variation(filtered_rps),
                    "latency_ms_p95_cv": coefficient_of_variation(filtered_p95),
                    "latency_ms_p99_cv": coefficient_of_variation(filtered_p99),
                },
            },
            "median": {
                "rps": statistics.median(filtered_rps),
                "latency_ms_p50": statistics.median(filtered_p50),
                "latency_ms_p95": statistics.median(filtered_p95),
                "latency_ms_p99": statistics.median(filtered_p99),
            },
        },
        "docker": docker_stats,
        "resources_normalized": {
            "memory_mb": parse_mem_to_mb(docker_stats.get("memory")),
            "cpu_percent": parse_cpu_percent(docker_stats.get("cpu")),
            "startup_ms": (warmup_first_success * 1000) if warmup_first_success is not None else None,
        },
    }

    args.out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    median = payload["benchmark"]["median"]
    print(
        f"OK {args.framework}: median_rps={median['rps']:.2f} "
        f"p50={median['latency_ms_p50']:.2f}ms "
        f"p95={median['latency_ms_p95']:.2f}ms "
        f"p99={median['latency_ms_p99']:.2f}ms"
    )


if __name__ == "__main__":
    main()
