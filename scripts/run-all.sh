#!/usr/bin/env bash
set -euo pipefail

frameworks=(modkit nestjs baseline wire fx "do")
raw_dir="${RESULTS_RAW_DIR:-results/latest/raw}"
mkdir -p "$raw_dir"
results_dir="${RESULTS_DIR:-$(dirname "$raw_dir")}"
fingerprint_file="${FINGERPRINT_FILE:-$results_dir/environment.fingerprint.json}"
manifest_file="${MANIFEST_FILE:-$results_dir/environment.manifest.json}"

python3 scripts/environment-manifest.py collect-fingerprint --out "$fingerprint_file"

for framework in "${frameworks[@]}"; do
  echo "=== Benchmarking: $framework ==="
  BENCHMARK_METADATA_MANAGED=1 bash scripts/run-single.sh "$framework"
done

python3 scripts/environment-manifest.py write-manifest --raw-dir "$raw_dir" --fingerprint "$fingerprint_file" --out "$manifest_file"

echo "Raw benchmark files generated in: $raw_dir"
