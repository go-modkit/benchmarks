# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-07T17:40:00+02:00
**Commit:** 46f84cd
**Branch:** feat/benchmark-repo-hardening

## OVERVIEW
Benchmark harness for API parity and performance comparison across framework implementations.
Correctness is enforced first (parity), then benchmark scripts generate raw metrics and reports.

## STRUCTURE
```text
benchmarks/
├── cmd/parity-test/          # Go parity runner + matcher/fixture tests
├── test/fixtures/parity/     # Parity seed + endpoint scenarios
├── scripts/                  # Parity-gated benchmark and report pipeline
├── docs/                     # Architecture + operational guides
├── .github/workflows/        # CI + CodeQL
├── apps/                     # Placeholder for framework app implementations
├── results/latest/           # Generated raw metrics, summary, report
├── Makefile
└── docker-compose.yml
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Run parity checks | `Makefile`, `scripts/parity-check.sh` | `PARITY_TARGET=... make parity-check` is canonical |
| Extend parity runner | `cmd/parity-test/main.go`, `cmd/parity-test/main_test.go` | Matcher semantics + fixture validation tests |
| Add/adjust contract cases | `test/fixtures/parity/scenarios/*.json` | Endpoint-grouped fixtures (`health`, `users-*`) |
| Change baseline test state | `test/fixtures/parity/seed.json` | Posted before scenarios when seed endpoint configured |
| Benchmark orchestration | `scripts/run-single.sh`, `scripts/run-all.sh` | Per-target parity gate then benchmark output emit |
| Reporting | `scripts/generate-report.py`, `results/latest/` | Builds `summary.json` and `report.md` from raw JSON |
| CI policy | `.github/workflows/ci.yml`, `.github/workflows/codeql.yml` | Semantic PR title check + Go tests + script smoke + CodeQL |

## CODE MAP
LSP project views unavailable in this environment (`no views`).
Use direct file map; Go entrypoint remains `cmd/parity-test/main.go` (`func main()`).

## CONVENTIONS
- Benchmark scripts are parity-gated per target: benchmark is skipped when health or parity fails.
- Raw benchmark outputs are one JSON file per framework under `results/latest/raw/`.
- Report generation is deterministic from raw artifacts (`summary.json`, `report.md`).
- CI runs three tracks: PR title semantics, Go tests, script/report smoke.

## ANTI-PATTERNS (THIS PROJECT)
- Do not benchmark before parity passes for the target implementation.
- Do not change matcher token semantics without updating fixture expectations and design doc.
- Do not treat generated files in `results/latest/` as hand-authored source-of-truth.

## UNIQUE STYLES
- Parity contract is fixture-first; runner logic is intentionally generic and target-agnostic.
- Scenarios stay endpoint-grouped (`users-*`, `health`) instead of a single aggregate fixture file.
- Benchmark scripts degrade gracefully by writing `skipped` records when targets are unavailable.

## COMMANDS
```bash
# Run full benchmark orchestration
make benchmark

# Generate benchmark report
make report

# Run unit tests
make test

# Run parity checks against a specific service
make parity-check-modkit
make parity-check-nestjs

# Generic parity invocation (set target URL)
PARITY_TARGET=http://localhost:3001 make parity-check

# Direct parity CLI invocation
go run ./cmd/parity-test -target http://localhost:3001 -fixtures test/fixtures/parity
```

## NOTES
- `apps/` is still a placeholder in this branch.
- `results/latest/` is generated output; contents vary between runs and environments.
