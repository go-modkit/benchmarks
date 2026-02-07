#!/usr/bin/env bash

setup_temp_results() {
  export TEST_TMPDIR
  TEST_TMPDIR="$(mktemp -d)"
  export RESULTS_DIR="$TEST_TMPDIR/results/latest"
  export RESULTS_RAW_DIR="$RESULTS_DIR/raw"
  mkdir -p "$RESULTS_RAW_DIR"
}

teardown_temp_results() {
  if [ -n "${TEST_TMPDIR:-}" ] && [ -d "$TEST_TMPDIR" ]; then
    rm -rf "$TEST_TMPDIR"
  fi
}
