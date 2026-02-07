# benchmarks

[![CI](https://github.com/go-modkit/benchmarks/actions/workflows/ci.yml/badge.svg)](https://github.com/go-modkit/benchmarks/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/go-modkit/benchmarks/branch/main/graph/badge.svg)](https://codecov.io/gh/go-modkit/benchmarks)
[![CodeQL](https://github.com/go-modkit/benchmarks/actions/workflows/codeql.yml/badge.svg)](https://github.com/go-modkit/benchmarks/actions/workflows/codeql.yml)
[![Go Report Card](https://goreportcard.com/badge/github.com/go-modkit/benchmarks)](https://goreportcard.com/report/github.com/go-modkit/benchmarks)
[![License](https://img.shields.io/github/license/go-modkit/benchmarks)](LICENSE)

Benchmark harness for framework parity and performance comparisons.

## What this repository does

- validates API behavior parity across implementations before performance runs
- stores declarative parity fixtures and seed data
- provides benchmark orchestration scripts and report generation

## Status & scope

- **Status**: Active benchmark harness with CI-enforced parity, schema checks, and quality policy checks.
- **Current targets**: `modkit`, `nestjs`, `baseline`, `wire`, `fx`, `do`.
- **Scope**: This repository publishes methodology, raw artifacts, and reproducible reports; it does not claim absolute winners across runtimes.
- **Primary artifact entrypoints**: `results/latest/report.md` and `results/latest/summary.json`.

## How to contribute benchmark targets

1. Implement a runnable service target under the project structure used by existing adapters.
2. Add or update parity fixtures in `test/fixtures/parity/` to keep behavior checks explicit.
3. Validate locally with `PARITY_TARGET=http://localhost:<port> make parity-check`.
4. Run benchmark flow and checks: `make benchmark`, `make report`, `make benchmark-schema-validate`, `make ci-benchmark-quality-check`.
5. Open a PR with reproducibility context and generated artifact references (see `CONTRIBUTING.md` and `docs/guides/benchmark-workflow.md`).

## How this complements modkit

This repository serves as the companion performance laboratory for [go-modkit/modkit](https://github.com/go-modkit/modkit). While modkit focuses on developer ergonomics and modular architecture, this harness ensures that those abstractions do not come at the cost of performance or correctness.

By maintaining a strict parity-gate, we ensure that every framework implementation compared here—including modkit—adheres to the same API contract before a single request is timed.

## Why trust these benchmarks

We prioritize correctness and reproducibility over "hero numbers":

- **Parity-Gated**: Benchmarks are automatically skipped if a target fails the API behavior contract. We only measure what is correct.
- **Reproducible**: All runs use Docker-based orchestration with pinned resource limits and standardized load profiles.
- **Transparent**: Raw metrics, environment fingerprints, and statistical variance are preserved for every run.
- **Policy-Driven**: Quality gates enforce statistical significance and schema validation for all artifacts.

For detailed execution details and fairness principles, see our [Methodology](METHODOLOGY.md) and [Benchmark Workflow](docs/guides/benchmark-workflow.md).

## Quickstart

Run parity against a local target:

```bash
PARITY_TARGET=http://localhost:3001 make parity-check
```

Run benchmark orchestration and generate a report:

```bash
make benchmark
make report
make benchmark-schema-validate
make ci-benchmark-quality-check
```

Benchmark/report flow enforces schema validation for raw and summary artifacts before quality gates.

Manual bounded benchmark workflow is available in GitHub Actions as `benchmark-manual`.
See `docs/guides/benchmark-workflow.md` for input bounds and execution details.

Use OSS measurement engine (optional):

```bash
BENCH_ENGINE=hyperfine make benchmark
```

## Tooling prerequisites

- Go (for `go test` and `benchstat`)
- Python 3
- hyperfine (optional benchmark engine)
- benchstat (`go install golang.org/x/perf/cmd/benchstat@latest`)
- go-patch-cover (`go install github.com/seriousben/go-patch-cover/cmd/go-patch-cover@latest`, for `make test-patch-coverage`)

## Repository layout

```text
benchmarks/
|- cmd/parity-test/           # Go parity CLI
|- test/fixtures/parity/      # seed + scenario contract fixtures
|- scripts/                   # benchmark/parity orchestration
|- docs/                      # design and operational guides
|- apps/                      # framework app implementations (placeholder)
`- results/                   # benchmark outputs (placeholder)
```

## Core policies

- parity is a gate: do not benchmark a target that fails parity
- fixture contract is source-of-truth for expected API behavior
- matcher changes require fixture updates and design doc updates

## Publication policy

- latest-results source of truth: `results/latest/summary.json` and `results/latest/report.md`
- report and summary are generated from `results/latest/raw/*.json` via `python3 scripts/generate-report.py`
- README must not publish standalone benchmark numbers; publication references must point to generated artifacts

### Fairness disclaimer (publication-wide)

- Language-vs-framework caveat: cross-language comparisons include runtime/ecosystem effects and are not framework-only deltas
- Cross-language interpretation must be treated as directional evidence, not absolute winner claims
- Parity failures invalidate performance interpretation until correctness is restored

## Documentation

**Design & Architecture:**
- `docs/design/002-api-parity-contract.md` - parity contract rationale
- `docs/architecture.md` - repository architecture and execution flow

**Guides:**
- `docs/guides/parity-contract.md` - fixture and matcher semantics
- `docs/guides/adding-scenarios.md` - how to add parity scenarios
- `docs/guides/benchmark-workflow.md` - benchmark and reporting flow
- `docs/guides/benchmark-publication-policy.md` - minimum disclosure for publishable results

**Governance:**
- `MAINTAINERS.md` - maintainership roles and triage expectations
- `CONTRIBUTING.md` - contribution process and validation commands
- `SECURITY.md` - security policy and vulnerability reporting

## Contributing

See `CONTRIBUTING.md` for contribution process and validation commands.
