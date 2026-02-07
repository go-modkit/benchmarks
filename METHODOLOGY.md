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
- policy file: `stats-policy.yaml`
- Python 3 report and normalization tooling in `scripts/`

## Baseline benchmark profile

- warmup requests: 100 (legacy engine path)
- benchmark requests per run: 300
- runs per target: 3 (median reported)

## Quality policy

- thresholds and required metrics are defined in `stats-policy.yaml`
- `make ci-benchmark-quality-check` enforces policy locally and in CI
- benchstat comparisons are evaluated against policy baseline framework (`baseline` by default)
- manual CI benchmark runs use bounded workflow inputs (`frameworks` subset, `runs` 1..10, `benchmark_requests` 50..1000)

## Reporting

- raw run outputs: `results/latest/raw/`
- normalized summary: `results/latest/summary.json`
- markdown report: `results/latest/report.md`
- quality summary: `results/latest/benchmark-quality-summary.json`
- optional tool artifacts: `results/latest/tooling/benchstat/*.txt`

## Interpretation guidance

- treat parity failures as correctness blockers, not performance regressions
- compare medians first, then inspect distribution variance
- use benchstat deltas and policy thresholds for pass/fail interpretation
- annotate environment drift (host type, CPU, memory, Docker version) in report notes
