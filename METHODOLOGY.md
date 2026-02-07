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
- Python 3 report generator (`scripts/generate-report.py`)

## Baseline benchmark profile

- warmup requests: 1000
- request threads: 12
- concurrent connections: 400
- run duration: 30s
- runs per target: 3 (median reported)

## Reporting

- raw run outputs: `results/latest/raw/`
- normalized summary: `results/latest/summary.json`
- markdown report: `results/latest/report.md`

## Interpretation guidance

- treat parity failures as correctness blockers, not performance regressions
- compare medians first, then inspect distribution variance
- annotate environment drift (host type, CPU, memory, Docker version) in report notes
