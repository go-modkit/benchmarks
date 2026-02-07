# Benchmark Report

Generated: `2026-01-01T00:00:00+00:00`

## Overview
- Total targets: 3
- Successful: 1
- Skipped: 2

## Results

| Framework | Status | Median RPS | P50 Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Notes |
|---|---:|---:|---:|---:|---:|---|
| modkit | ok | 600.00 | 1.50 | 2.50 | 2.80 |  |
| nestjs | skipped | - | - | - | - | target health endpoint unavailable |
| wire | skipped | - | - | - | - | parity check failed |

## Fairness Disclaimer

- Language-vs-framework caveat: cross-language results include runtime and ecosystem effects and must not be treated as framework-only deltas.
- Cross-language baseline: compare implementations with equivalent API behavior, workload profile, and environment constraints before drawing conclusions.

## Anti-Misinterpretation Guidance

- Do not rank frameworks across languages as absolute winners; use results as scenario-specific signals.
- Treat large cross-language deltas as prompts for deeper profiling (runtime, I/O, GC, and dependency effects), not as standalone product claims.
- Parity failures invalidate performance interpretation until correctness is restored.

## Raw Artifacts

- Raw JSON: `results/latest/raw/*.json`
- Summary JSON: `results/latest/summary.json`
