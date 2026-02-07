#!/usr/bin/env bash
set -euo pipefail

frameworks=(modkit nestjs baseline wire fx "do")
raw_dir="${RESULTS_RAW_DIR:-results/latest/raw}"
results_dir="${RESULTS_DIR:-$(dirname "$raw_dir")}"
fingerprint_file="${FINGERPRINT_FILE:-$results_dir/environment.fingerprint.json}"
manifest_file="${MANIFEST_FILE:-$results_dir/environment.manifest.json}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
results_root="$repo_root/results/latest"
source "$script_dir/lib.sh"

results_root_abs="$(resolve_path "$results_root")"
raw_dir_abs="$(resolve_path "$raw_dir")"
results_dir_abs="$(resolve_path "$results_dir")"
fingerprint_file_abs="$(resolve_path "$fingerprint_file")"
manifest_file_abs="$(resolve_path "$manifest_file")"

ensure_path_under_root "RESULTS_RAW_DIR" "$raw_dir_abs" "$results_root_abs"
ensure_path_under_root "RESULTS_DIR" "$results_dir_abs" "$results_root_abs"
ensure_path_under_root "FINGERPRINT_FILE" "$fingerprint_file_abs" "$results_root_abs"
ensure_path_under_root "MANIFEST_FILE" "$manifest_file_abs" "$results_root_abs"

raw_dir="$raw_dir_abs"
results_dir="$results_dir_abs"
fingerprint_file="$fingerprint_file_abs"
manifest_file="$manifest_file_abs"

mkdir -p "$raw_dir"

python3 scripts/environment-manifest.py collect-fingerprint --out "$fingerprint_file"

for framework in "${frameworks[@]}"; do
  echo "=== Benchmarking: $framework ==="
  BENCHMARK_METADATA_MANAGED=1 bash scripts/run-single.sh "$framework"
done

python3 scripts/validate-result-schemas.py raw-check --raw-dir "$raw_dir"

python3 scripts/environment-manifest.py write-manifest --raw-dir "$raw_dir" --fingerprint "$fingerprint_file" --out "$manifest_file"

echo "Raw benchmark files generated in: $raw_dir"
