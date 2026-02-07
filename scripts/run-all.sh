#!/usr/bin/env bash
set -euo pipefail

frameworks=(modkit nestjs baseline wire fx "do")
raw_dir="${RESULTS_RAW_DIR:-results/latest/raw}"
mkdir -p "$raw_dir"

for framework in "${frameworks[@]}"; do
  echo "=== Benchmarking: $framework ==="
  bash scripts/run-single.sh "$framework"
done

echo "Raw benchmark files generated in: $raw_dir"
