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
source "$script_dir/lib.sh"

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

ensure_path_under_root "FINGERPRINT_FILE" "$fingerprint_file_abs" "$results_root_abs"
ensure_path_under_root "MANIFEST_FILE" "$manifest_file_abs" "$results_root_abs"

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
    "schema_version": "raw-v1",
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
    "schema_version": "raw-v1",
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

python3 scripts/benchmark-measure.py \
  --framework "$framework" \
  --target "$target" \
  --endpoint "$endpoint" \
  --warmup-requests "$warmup_requests" \
  --benchmark-requests "$benchmark_requests" \
  --runs "$runs" \
  --out-file "$out_file" \
  --parity-result "$parity_result" \
  --engine "${BENCH_ENGINE:-legacy}"

write_manifest
