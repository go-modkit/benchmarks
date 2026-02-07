#!/usr/bin/env bash
set -euo pipefail

framework="${1:-}"
if [[ -z "$framework" ]]; then
  echo "Usage: bash scripts/run-single.sh <framework>" >&2
  exit 1
fi

case "$framework" in
  modkit) target="${TARGET:-http://localhost:3001}" ;;
  nestjs) target="${TARGET:-http://localhost:3002}" ;;
  baseline) target="${TARGET:-http://localhost:3003}" ;;
  wire) target="${TARGET:-http://localhost:3004}" ;;
  fx) target="${TARGET:-http://localhost:3005}" ;;
  do) target="${TARGET:-http://localhost:3006}" ;;
  *)
    echo "Unknown framework: $framework" >&2
    exit 1
    ;;
esac

raw_dir="${RESULTS_RAW_DIR:-results/latest/raw}"
metadata_managed="${BENCHMARK_METADATA_MANAGED:-0}"
results_dir="${RESULTS_DIR:-$(dirname "$raw_dir")}"
fingerprint_file="${FINGERPRINT_FILE:-$results_dir/environment.fingerprint.json}"
manifest_file="${MANIFEST_FILE:-$results_dir/environment.manifest.json}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
results_root="$repo_root/results/latest"
expected_raw_dir="$results_root/raw"

resolve_path() {
  python3 - <<'PY' "$1"
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
}

raw_dir_abs="$(resolve_path "$raw_dir")"
results_dir_abs="$(resolve_path "$results_dir")"
fingerprint_file_abs="$(resolve_path "$fingerprint_file")"
manifest_file_abs="$(resolve_path "$manifest_file")"
results_root_abs="$(resolve_path "$results_root")"
expected_raw_abs="$(resolve_path "$expected_raw_dir")"

if [[ "$raw_dir_abs" != "$expected_raw_abs" ]]; then
  echo "RESULTS_RAW_DIR must resolve to $expected_raw_abs (got: $raw_dir_abs)" >&2
  exit 1
fi

if [[ "$results_dir_abs" != "$results_root_abs" ]]; then
  echo "RESULTS_DIR must resolve to $results_root_abs (got: $results_dir_abs)" >&2
  exit 1
fi

case "$fingerprint_file_abs" in
  "$results_root_abs"|"$results_root_abs"/*) ;;
  *)
    echo "FINGERPRINT_FILE must be under $results_root_abs (got: $fingerprint_file_abs)" >&2
    exit 1
    ;;
esac

case "$manifest_file_abs" in
  "$results_root_abs"|"$results_root_abs"/*) ;;
  *)
    echo "MANIFEST_FILE must be under $results_root_abs (got: $manifest_file_abs)" >&2
    exit 1
    ;;
esac

raw_dir="$expected_raw_abs"
results_dir="$results_root_abs"
fingerprint_file="$fingerprint_file_abs"
manifest_file="$manifest_file_abs"
out_file="$raw_dir/${framework}.json"

mkdir -p "$raw_dir"

write_manifest() {
  if [[ "$metadata_managed" == "1" ]]; then
    return
  fi
  python3 scripts/environment-manifest.py write-manifest --raw-dir "$raw_dir" --fingerprint "$fingerprint_file" --out "$manifest_file"
}

if [[ "$metadata_managed" != "1" ]]; then
  python3 scripts/environment-manifest.py collect-fingerprint --out "$fingerprint_file"
fi

if ! curl -fsS "$target/health" >/dev/null 2>&1; then
  python3 - <<'PY' "$framework" "$target" "$out_file"
import json, sys
framework, target, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {
    "framework": framework,
    "target": target,
    "status": "skipped",
    "reason": "target health endpoint unavailable",
}
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print(f"SKIP {framework}: health endpoint unavailable")
PY
  write_manifest
  exit 0
fi

if PARITY_TARGET="$target" bash scripts/parity-check.sh >/dev/null; then
  parity_result="passed"
else
  python3 - <<'PY' "$framework" "$target" "$out_file"
import json, sys
framework, target, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {
    "framework": framework,
    "target": target,
    "status": "skipped",
    "reason": "parity check failed",
}
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print(f"SKIP {framework}: parity failed")
PY
  write_manifest
  exit 0
fi

warmup_requests="${WARMUP_REQUESTS:-100}"
benchmark_requests="${BENCHMARK_REQUESTS:-300}"
runs="${BENCHMARK_RUNS:-3}"
endpoint="${BENCHMARK_ENDPOINT:-/health}"

python3 - <<'PY' "$framework" "$target" "$endpoint" "$warmup_requests" "$benchmark_requests" "$runs" "$out_file" "$parity_result"
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

framework, target, endpoint, warmup, requests, runs, out_file, parity_result = sys.argv[1:9]
warmup = int(warmup)
requests = int(requests)
runs = int(runs)
url = target.rstrip("/") + endpoint


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

def request_once():
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            r.read()
        return time.perf_counter() - start
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"http_error status={exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"url_error reason={exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"request_error {exc}") from exc

# Warmup: tolerate transient failures.
warmup_first_success = None
for _ in range(warmup):
    try:
        duration = request_once()
        if warmup_first_success is None:
            warmup_first_success = duration
    except Exception:
        pass

run_stats = []
for _ in range(runs):
    durations = []
    for _ in range(requests):
        try:
            durations.append(request_once())
        except Exception:
            pass
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

if not run_stats:
    payload = {
        "framework": framework,
        "target": target,
        "status": "skipped",
        "reason": "benchmark requests failed",
        "parity": parity_result,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"SKIP {framework}: benchmark requests failed")
    raise SystemExit(0)

median_rps = statistics.median([r["rps"] for r in run_stats])
median_p50 = statistics.median([r["latency_ms_p50"] for r in run_stats])
median_p95 = statistics.median([r["latency_ms_p95"] for r in run_stats])
median_p99 = statistics.median([r["latency_ms_p99"] for r in run_stats])

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

payload = {
    "framework": framework,
    "target": target,
    "status": "ok",
    "parity": parity_result,
    "metric_units": {
        "throughput": "requests_per_second",
        "latency": "milliseconds",
        "memory": "mb",
        "cpu": "percent",
        "startup": "milliseconds",
    },
    "benchmark": {
        "endpoint": endpoint,
        "warmup_requests": warmup,
        "requests_per_run": requests,
        "runs": runs,
        "run_stats": run_stats,
        "median": {
            "rps": median_rps,
            "latency_ms_p50": median_p50,
            "latency_ms_p95": median_p95,
            "latency_ms_p99": median_p99,
        },
    },
    "docker": docker_stats,
    "resources_normalized": {
        "memory_mb": parse_mem_to_mb(docker_stats.get("memory")),
        "cpu_percent": parse_cpu_percent(docker_stats.get("cpu")),
        "startup_ms": (warmup_first_success * 1000) if warmup_first_success is not None else None,
    },
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print(f"OK {framework}: median_rps={median_rps:.2f} p50={median_p50:.2f}ms p95={median_p95:.2f}ms p99={median_p99:.2f}ms")
PY

write_manifest
