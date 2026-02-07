# PROJECT KNOWLEDGE BASE - cmd/parity-test

**Generated:** 2026-02-07T17:40:00+02:00
**Commit:** 46f84cd
**Branch:** feat/benchmark-repo-hardening

## OVERVIEW
Go parity runner CLI that validates HTTP contract behavior against fixture scenarios.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| CLI flags / execution flow | `cmd/parity-test/main.go` (`func main`) | Target URL, fixture dir, seed endpoint, timeout wiring |
| Seed bootstrap behavior | `cmd/parity-test/main.go` (`seedTarget`) | Optional pre-run POST to seed endpoint |
| Scenario request execution | `cmd/parity-test/main.go` (`runScenario`) | Request construction, status/header/body assertion |
| Body matcher semantics | `cmd/parity-test/main.go` (`compareValue`, `matchStringValue`) | Recursive object/array checks + token matching |
| Matcher primitives | `cmd/parity-test/main.go` (`isNumber`, `isISO8601`) | Type/format checks used by tokens |
| Unit coverage for matcher + fixtures | `cmd/parity-test/main_test.go` | Token behavior, recursive compare, fixture shape guards |

## CONVENTIONS
- Exit behavior is strict: missing target/fixtures or any failed scenario returns non-zero.
- Scenario files are loaded from `<fixtures>/scenarios/*.json` and processed in sorted order.
- Header checks verify expected keys exist and values match token-aware string matching.
- Body checks are partial-object style: expected keys must exist; extra keys in actual object are tolerated.
- Test suite treats fixture health as contract integrity (JSON validity, names, status/path requirements).

## ANTI-PATTERNS (THIS DIRECTORY)
- Do not silently swallow request/JSON parse errors; keep explicit failure messages.
- Do not turn seed failures into hard exits by default; current contract treats them as warnings.
- Do not add service-specific logic (framework names, per-app branches); runner must stay target-agnostic.
- Do not loosen matcher tests when adding tokens; add explicit positive + negative cases.

## COMMANDS
```bash
# Run parity CLI directly
go run ./cmd/parity-test -target http://localhost:3001 -fixtures test/fixtures/parity

# Same via make wrapper
PARITY_TARGET=http://localhost:3001 make parity-check
```

## NOTES
- Runtime remains intentionally small; tests carry most semantic guardrails.
