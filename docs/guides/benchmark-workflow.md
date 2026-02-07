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

## Parity gate

Benchmark scripts must run parity first for each target. If parity fails, skip benchmark for that target and record the skip reason.

## Artifacts

- `results/latest/raw/*.json` - raw benchmark outputs
- `results/latest/summary.json` - normalized summary
- `results/latest/report.md` - markdown report

## Reproducibility notes

- run from a clean working tree when possible
- keep runtime versions stable
- include host and Docker metadata in report notes
