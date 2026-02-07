#!/usr/bin/env bats

load "helpers/load.bash"

setup() {
  setup_temp_results
}

teardown() {
  teardown_temp_results
}

@test "run-single rejects unknown framework" {
  run bash scripts/run-single.sh unknown-framework
  [ "$status" -ne 0 ]
}

@test "run-all rejects raw dir outside results/latest" {
  run env RESULTS_RAW_DIR="/tmp" bash scripts/run-all.sh
  [ "$status" -ne 0 ]
}
