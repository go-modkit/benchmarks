# Benchmark Workflow

## Prerequisites

- targets available locally or via Docker Compose
- parity contract fixtures up to date

## Standard run

```bash
make benchmark
make report
```

## Per-target run

```bash
make benchmark-modkit
make benchmark-nestjs
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
- `results/latest/summary.json` - normalized summary
- `results/latest/report.md` - markdown report

## Reproducibility notes

- run from a clean working tree when possible
- keep runtime versions stable
- include host and Docker metadata in report notes
