# PROJECT KNOWLEDGE BASE - test/fixtures/parity

**Generated:** 2026-02-07T17:40:00+02:00
**Commit:** 46f84cd
**Branch:** feat/benchmark-repo-hardening

## OVERVIEW
Golden parity contract fixtures: deterministic seed data plus endpoint scenario expectations.

## STRUCTURE
```text
test/fixtures/parity/
├── seed.json                  # Preloaded baseline records
└── scenarios/
    ├── health.json            # Liveness contract
    ├── users-create.json      # POST /users success + validation failures
    ├── users-read.json        # GET list/detail behavior
    ├── users-update.json      # PATCH/PUT behavior and validation
    └── users-delete.json      # DELETE behavior
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Change baseline dataset | `test/fixtures/parity/seed.json` | Sent to seed endpoint before scenarios |
| Add user create cases | `test/fixtures/parity/scenarios/users-create.json` | Includes success and invalid payload paths |
| Adjust read contracts | `test/fixtures/parity/scenarios/users-read.json` | Collection/detail response expectations |
| Adjust update contracts | `test/fixtures/parity/scenarios/users-update.json` | Mutation behavior and error shape checks |
| Adjust delete contracts | `test/fixtures/parity/scenarios/users-delete.json` | Deletion idempotency/not-found behavior |
| Health contract | `test/fixtures/parity/scenarios/health.json` | Minimal service readiness check |

## CONVENTIONS
- Each file is a JSON array of scenarios with `name`, `request`, and `response` blocks.
- `request.method` defaults to `GET` only if omitted by runner logic.
- `response.status` is mandatory and exact.
- Use matcher tokens where values are dynamic: `@any_number`, `@is_iso8601`.
- Tokens can appear as full values or embedded inside strings (for example `/users/@any_number`).
- Fixture schema sanity is now tested in `cmd/parity-test/main_test.go` (`TestParityFixtures_AreWellFormed`).

## ANTI-PATTERNS (THIS DIRECTORY)
- Do not encode implementation-specific IDs/timestamps as fixed literals when token matchers are intended.
- Do not mix unrelated endpoint domains into one scenario file; keep endpoint-grouped fixture files.
- Do not change expected error envelope casually; parity compares API contract, not internal implementation details.

## NOTES
- `docs/design/002-api-parity-contract.md` documents the intent behind these fixtures; update both when changing contract semantics.
- `scripts/run-single.sh` parity-gates benchmark execution using these fixtures before any load run.
