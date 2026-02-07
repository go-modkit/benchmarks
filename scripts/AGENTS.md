# PROJECT KNOWLEDGE BASE - scripts

**Generated:** 2026-02-07T17:40:00+02:00
**Commit:** 46f84cd
**Branch:** feat/benchmark-repo-hardening

## OVERVIEW
Operational scripts for parity-gated benchmarking and report generation.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Direct parity invocation wrapper | `scripts/parity-check.sh` | Calls Go parity CLI with target/fixtures/env wiring |
| Run one framework benchmark | `scripts/run-single.sh` | Health probe -> parity gate -> benchmark or skip JSON |
| Run full framework matrix | `scripts/run-all.sh` | Iterates `modkit,nestjs,baseline,wire,fx,do` |
| Generate summary/report | `scripts/generate-report.py` | Reads `results/latest/raw/*.json` and writes summary/report |

## CONVENTIONS
- Shell scripts use `set -euo pipefail` and fail fast.
- Each framework emits exactly one raw JSON artifact under `results/latest/raw/`.
- Unavailable targets are not treated as hard failures; scripts write `status: skipped` records.
- `run-single.sh` must execute parity before any load sampling.
- Report generation is deterministic from raw JSON only.

## ANTI-PATTERNS
- Do not benchmark a target directly without invoking parity gate logic.
- Do not silently discard skip/failure context; encode a reason in raw JSON.
- Do not bake framework-specific behavior into generic report generation.
- Do not write to paths outside `results/latest/` from these scripts.

## COMMANDS
```bash
bash scripts/parity-check.sh
bash scripts/run-single.sh modkit
bash scripts/run-all.sh
python3 scripts/generate-report.py
```
