# Methodology

## Fairness principles

- all implementations must expose equivalent API behavior validated by parity tests
- identical endpoint semantics: status, headers, and body contract
- identical seed state before parity and benchmark runs
- identical load profile for each benchmark target

## Benchmark gate

1. Start target service
2. Wait for readiness endpoint
3. Run parity checks against target
4. Only if parity passes, run load benchmark
5. Persist raw metrics and summary artifacts

## Runtime environment

- Docker + Docker Compose for service orchestration
- Go parity runner (`cmd/parity-test`)
- shell scripts in `scripts/` for orchestration
- `hyperfine` benchmark engine (optional via `BENCH_ENGINE=hyperfine`)
- `benchstat` statistical comparison for quality gates
- policy file: `stats-policy.json`
- Python 3 report and normalization tooling in `scripts/`

## Baseline benchmark profile

- warmup requests: 100 (legacy engine path)
- benchmark requests per run: 300
- runs per target: 3 (median reported)

## Quality policy

- thresholds and required metrics are defined in `stats-policy.json`
- `make ci-benchmark-quality-check` enforces policy locally and in CI
- benchstat comparisons are evaluated against policy baseline framework (`baseline` by default)
- manual CI benchmark runs use bounded workflow inputs (`frameworks` subset, `runs` 1..10, `benchmark_requests` 50..1000)

## Reporting

- raw run outputs: `results/latest/raw/`
- normalized summary: `results/latest/summary.json`
- markdown report: `results/latest/report.md`
- quality summary: `results/latest/benchmark-quality-summary.json`
- optional tool artifacts: `results/latest/tooling/benchstat/*.txt`

## Methodology changelog policy

### Update rules

- update this changelog whenever benchmark process, tooling, schema, thresholds, runtime constraints, or interpretation rules change
- classify each entry as `comparability-impacting` or `non-comparability-impacting`
- for `comparability-impacting` changes, include migration notes and baseline reset guidance
- do not publish new benchmark claims without a corresponding changelog entry when methodology or version changed

### Entry format

Use one row per change with required fields:

`version | date (UTC) | change_type | summary | comparability_impact | required_action`

### Changelog

| version | date (UTC) | change_type | summary | comparability_impact | required_action |
|---|---|---|---|---|---|
| 1.1.0 | 2026-02-07 | policy | Added publication fairness disclaimer template and README/report sync policy checks | comparability-impacting | Rebaseline external comparisons and reference this version in publication notes |
| 1.0.0 | 2026-02-05 | baseline | Established parity-gated benchmark workflow, schema validation, and quality gates | comparability-impacting | Treat pre-1.0 outputs as non-comparable to current policy |

## Interpretation guidance

- treat parity failures as correctness blockers, not performance regressions
- compare medians first, then inspect distribution variance
- use benchstat deltas and policy thresholds for pass/fail interpretation
- annotate environment drift (host type, CPU, memory, Docker version) in report notes
