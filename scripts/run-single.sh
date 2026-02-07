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
mkdir -p "$raw_dir"
out_file="$raw_dir/${framework}.json"

metadata_managed="${BENCHMARK_METADATA_MANAGED:-0}"
results_dir="${RESULTS_DIR:-$(dirname "$raw_dir")}"
fingerprint_file="${FINGERPRINT_FILE:-$results_dir/environment.fingerprint.json}"
manifest_file="${MANIFEST_FILE:-$results_dir/environment.manifest.json}"

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
for _ in range(warmup):
    try:
        request_once()
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
        },
    },
    "docker": docker_stats,
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print(f"OK {framework}: median_rps={median_rps:.2f} p50={median_p50:.2f}ms p95={median_p95:.2f}ms")
PY

write_manifest
