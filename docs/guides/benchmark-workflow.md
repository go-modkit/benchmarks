# Benchmark Workflow

## Prerequisites

- targets available locally or via Docker Compose
- parity contract fixtures up to date
- benchmark quality tools installed locally:
  - `hyperfine` (for `BENCH_ENGINE=hyperfine`)
  - `benchstat` (`go install golang.org/x/perf/cmd/benchstat@latest`)

## Standard run

```bash
make benchmark
make report
make benchmark-schema-validate
```

## Per-target run

```bash
make benchmark-modkit
make benchmark-nestjs
```

Per-target runs also emit `results/latest/environment.fingerprint.json` and `results/latest/environment.manifest.json`.

Optional OSS measurement engine:

```bash
BENCH_ENGINE=hyperfine make benchmark
```

## Docker resource limits

Framework services use shared default limits from `docker-compose.yml`:

- CPU: `BENCHMARK_CPU_LIMIT` (default `1.00`)
- memory: `BENCHMARK_MEMORY_LIMIT` (default `1024m`)

Override for local experimentation:

```bash
BENCHMARK_CPU_LIMIT=2.00 BENCHMARK_MEMORY_LIMIT=1536m docker compose up --build
```

## Parity gate

Benchmark scripts must run parity first for each target. If parity fails, skip benchmark for that target and record the skip reason.

## Artifacts

- `results/latest/raw/*.json` - raw benchmark outputs
- `results/latest/environment.fingerprint.json` - runtime and toolchain versions for the run
- `results/latest/environment.manifest.json` - timestamped runner metadata and result index
- `results/latest/summary.json` - normalized summary
- `results/latest/report.md` - markdown report
- `results/latest/benchmark-quality-summary.json` - policy quality gate output
- `results/latest/tooling/benchstat/*.txt` - benchstat comparison outputs
- `schemas/benchmark-raw-v1.schema.json` - raw benchmark artifact contract
- `schemas/benchmark-summary-v1.schema.json` - summary artifact contract

## Quality checks

```bash
make benchmark-schema-validate
make benchmark-stats-check
make benchmark-variance-check
make benchmark-benchstat-check
make ci-benchmark-quality-check
```

Quality thresholds and required metrics are versioned in `stats-policy.yaml`.

## Reproducibility notes

- run from a clean working tree when possible
- keep runtime versions stable
- include host and Docker metadata in report notes
