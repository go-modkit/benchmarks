# Architecture

## Overview

The repository has two core planes:

- correctness plane: parity runner + fixture contract
- performance plane: benchmark orchestration + reporting

Correctness runs before performance.

## Components

```text
cmd/parity-test/         parity CLI runtime
test/fixtures/parity/    seed + scenario contract files
scripts/                 benchmark/parity orchestration wrappers
results/latest/          benchmark outputs and generated report
```

## Parity flow

1. Load `seed.json` (if configured)
2. Discover `scenarios/*.json`
3. Execute each scenario request
4. Compare status, headers, and body recursively
5. Aggregate failures and exit non-zero on any mismatch

## Matcher semantics

- `@any_number`: accepts numeric values (number types or numeric strings)
- `@is_iso8601`: accepts RFC3339/RFC3339Nano timestamps
- tokens can appear as full values or interpolated inside strings

## Benchmark flow

1. Launch target services
2. Run parity checks per target
3. Run load benchmarks for parity-passing targets (`legacy` engine or `hyperfine`)
4. Normalize and save raw outputs
5. Run policy quality gates (`stats-policy.json` + benchstat)
6. Build `summary.json`
7. Generate `report.md`

## Failure model

- parity failures do not stop fixture file iteration; they aggregate and fail at the end
- benchmark runs should short-circuit per target if parity fails
- report generation should tolerate partial target results and mark skipped targets
- quality gate summary should always be emitted, including all-skipped smoke runs
