# benchmarks

Benchmark harness for framework parity and performance comparisons.

## What this repository does

- validates API behavior parity across implementations before performance runs
- stores declarative parity fixtures and seed data
- provides benchmark orchestration scripts and report generation

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

## Documentation

- `docs/design/002-api-parity-contract.md` - parity contract rationale
- `docs/architecture.md` - repository architecture and execution flow
- `docs/guides/parity-contract.md` - fixture and matcher semantics
- `docs/guides/adding-scenarios.md` - how to add parity scenarios
- `docs/guides/benchmark-workflow.md` - benchmark and reporting flow

## Contributing

See `CONTRIBUTING.md` for contribution process and validation commands.
