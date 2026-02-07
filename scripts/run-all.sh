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

resolve_path() {
  python3 - <<'PY' "$1"
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
}

results_root_abs="$(resolve_path "$results_root")"
raw_dir_abs="$(resolve_path "$raw_dir")"
results_dir_abs="$(resolve_path "$results_dir")"
fingerprint_file_abs="$(resolve_path "$fingerprint_file")"
manifest_file_abs="$(resolve_path "$manifest_file")"

case "$raw_dir_abs" in
  "$results_root_abs"|"$results_root_abs"/*) ;;
  *)
    echo "RESULTS_RAW_DIR must be under $results_root_abs (got: $raw_dir_abs)" >&2
    exit 1
    ;;
esac

case "$results_dir_abs" in
  "$results_root_abs"|"$results_root_abs"/*) ;;
  *)
    echo "RESULTS_DIR must be under $results_root_abs (got: $results_dir_abs)" >&2
    exit 1
    ;;
esac

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

python3 scripts/environment-manifest.py write-manifest --raw-dir "$raw_dir" --fingerprint "$fingerprint_file" --out "$manifest_file"

echo "Raw benchmark files generated in: $raw_dir"
