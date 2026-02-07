#!/usr/bin/env bash
set -euo pipefail

target="${TARGET:-}" fixtures="${PARITY_FIXTURES:-test/fixtures/parity}" seed_endpoint="${PARITY_SEED_ENDPOINT:-/debug/parity/seed}" timeout="${PARITY_TIMEOUT:-5s}"

if [[ -z "$target" ]]; then
  echo "TARGET environment variable required (e.g. TARGET=http://localhost:3001)" >&2
  exit 1
fi

PARITY_BIN="$(cd "$(dirname "$0")" && go env GOPATH)/bin"

cmd=(go run ./cmd/parity-test -target "$target" -fixtures "$fixtures" -seed-endpoint "$seed_endpoint" -timeout "$timeout")
exec "${cmd[@]}"
