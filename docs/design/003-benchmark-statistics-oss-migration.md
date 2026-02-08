# Design 003: OSS-Based Benchmark Statistics and CI Quality Gates

## 1. Goal
Replace custom statistical processing logic with OSS benchmark/statistics tooling while preserving repository-specific benchmark orchestration, parity-first gating, and artifact contracts.

**Why:**
- OSS tools reduce maintenance burden and improve methodological confidence.
- Statistical quality rules should be explicit, versioned, and enforced consistently in local runs and CI.
- Existing result/report paths should stay stable to avoid breaking downstream workflows.

## 2. Scope
In:
1. Integrate `hyperfine` as the benchmark measurement engine.
2. Integrate `benchstat` for statistical pass/fail checks.
3. Add a versioned policy file (`stats-policy.json`) for thresholds and rules.
4. Keep `results/latest/*` artifacts stable for summary/report consumers.
5. Update docs to reflect the new measurement and quality gate model.

Out:
1. Replacing parity contract behavior or matcher semantics.
2. Dashboard or visualization redesign.
3. Framework-specific performance tuning unrelated to methodology.

## 3. Non-Goals
1. Rewriting the benchmark orchestrator from scratch.
2. Removing all custom scripts (thin adapters/orchestration remain expected).
3. Changing issue-driven CI policy outside benchmark quality gates.

## 4. Architecture

### 4.1. Target Flow
1. **Parity Gate (existing behavior):** health check -> parity check per target.
2. **Measurement:** run benchmark samples using `hyperfine`.
3. **Normalization:** transform tool-native output into repo raw schema.
4. **Reporting:** generate `summary.json` and `report.md` from normalized artifacts.
5. **Quality Gate:** run policy checks (`benchstat`, variance thresholds, publication checks) on generated artifacts.

### 4.2. What Remains Custom
1. Framework matrix orchestration and target routing.
2. Parity-first skip behavior and skip reason recording.
3. Artifact shaping for `results/latest/raw/*.json` and report pipeline compatibility.

### 4.3. What Moves to OSS
1. Run scheduling/statistical sampling mechanics -> `hyperfine`.
2. Statistical comparison/significance logic -> `benchstat`.

## 5. Policy Design

### 5.1. `stats-policy.json` (single source of truth)
Policy fields:
- significance (`alpha`), default `0.05`
- minimum run count per target
- regression thresholds by metric (percent-based)
- required metrics (must exist in normalized artifact)
- skip handling rules (`skipped` targets do not fail run by themselves)

### 5.2. Policy Enforcement Rules
1. No pass/fail decision without policy file.
2. Local and CI commands must use the same policy file.
3. Violations must emit actionable diagnostics per framework/metric.
4. Quality summary output is mandatory even when all targets are skipped.

## 6. Artifact Contract

### 6.1. Stable Artifacts (must remain)
- `results/latest/raw/*.json`
- `results/latest/summary.json`
- `results/latest/report.md`
- `results/latest/benchmark-quality-summary.json`

### 6.2. Optional Tool-Native Artifacts
- `results/latest/tooling/hyperfine/*.json`
- `results/latest/tooling/benchstat/*.txt`

## 7. CI Design
CI keeps `make ci-benchmark-quality-check` as the primary gate and:
1. runs benchmark pipeline,
2. runs quality policy check,
3. uploads benchmark quality summary and tool-native outputs as artifacts,
4. fails only on policy violations (not on expected parity/health skips).

## 8. Migration Plan

### Phase A: Policy + Interfaces
1. Add `stats-policy.json`.
2. Define normalized schema compatibility contract.
3. Add adapter interfaces without changing default execution path.

### Phase B: OSS Integration in Parallel
1. Add `BENCH_ENGINE=hyperfine` execution path.
2. Normalize tool output to existing raw schema.
3. Add `benchstat` gate in report-only mode.

### Phase C: Gate Cutover
1. Switch `ci-benchmark-quality-check` to policy-enforcing mode.
2. Keep artifact outputs and names stable.

### Phase D: Cleanup
1. Remove superseded custom variance/outlier math.
2. Retain thin orchestration and normalization glue only.

## 9. Risks and Mitigations
1. **Risk:** command-level timing differs from request-loop timing.
   **Mitigation:** add a benchmark runner wrapper so each invocation is semantically consistent.
2. **Risk:** policy too strict causes unstable CI.
   **Mitigation:** ramp from report-only to enforced mode after calibration window.
3. **Risk:** artifact drift breaks report tooling.
   **Mitigation:** keep normalized schema contract stable and versioned.

## 10. Verification Plan
Required local verification before merge:
```bash
go test ./... -coverprofile=coverage.out -covermode=atomic
make benchmark
make report
make ci-benchmark-quality-check
```

Quality acceptance:
1. policy file is loaded and applied in local + CI runs,
2. quality summary artifact is generated every run,
3. parity-first skip semantics remain unchanged,
4. report generation remains deterministic from normalized artifacts.

## 11. Documentation Update Plan
The implementation for this design must include synchronized doc updates:
1. `METHODOLOGY.md` - replace custom-stat narrative with OSS toolchain and policy model.
2. `docs/guides/benchmark-workflow.md` - add required tools, execution flow, and artifact references.
3. `docs/architecture.md` - update performance plane and quality gate stage boundaries.
4. `README.md` - refresh quickstart/validation commands and tool prerequisites.
5. `docs/design/003-benchmark-statistics-oss-migration.md` - keep as design source of truth.

## 12. Rollback Strategy
If OSS migration introduces instability:
1. toggle back to legacy engine path,
2. keep parity and artifact generation operational,
3. continue emitting quality summary with explicit `mode: legacy` marker,
4. re-enable OSS path after threshold recalibration.
