# PROJECT KNOWLEDGE BASE - docs/guides

**Generated:** 2026-02-07T17:40:00+02:00
**Commit:** 46f84cd
**Branch:** feat/benchmark-repo-hardening

## OVERVIEW
Operator-facing guides for parity contract usage, scenario authoring, and benchmark workflow.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Understand fixture semantics | `docs/guides/parity-contract.md` | Request/response schema and matcher tokens |
| Add or modify scenarios safely | `docs/guides/adding-scenarios.md` | Endpoint-grouped workflow + checklist |
| Run benchmark pipeline | `docs/guides/benchmark-workflow.md` | Standard, per-target, and artifact expectations |
| Publish benchmark results | `docs/guides/benchmark-publication-policy.md` | Minimum disclosure for publishable results |
| View maintainership info | `MAINTAINERS.md` | Roles, triage SLA, and escalation |


## CONVENTIONS
- Keep guides procedural and command-oriented.
- Reference canonical files/commands instead of duplicating full implementation details.
- Prefer policy statements that match executable behavior (parity gate, skip records).

## ANTI-PATTERNS
- Do not restate root README sections verbatim.
- Do not document behavior that scripts or CLI do not implement.
- Do not embed environment-specific benchmark numbers in guide files.

## COMMANDS
```bash
PARITY_TARGET=http://localhost:3001 make parity-check
make benchmark
make report
```

## NOTES
- Keep this directory focused on operator workflows; conceptual rationale stays in `docs/design/` and `docs/architecture.md`.
- Update guides when script interfaces or required environment variables change.
