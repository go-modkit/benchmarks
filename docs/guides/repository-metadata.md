# Repository Metadata Profile

This document defines the GitHub repository metadata for the `benchmarks` project. Maintaining accurate metadata ensures discoverability and clear positioning within the `go-modkit` ecosystem.

## Metadata Profile

| Field | Value |
|-------|-------|
| **Description** | Parity-gated benchmark harness for API framework performance comparison. Ensures correctness via declarative contract fixtures before measuring throughput and latency. |
| **Topics** | `go`, `benchmark`, `api-parity`, `performance-testing`, `reproducibility`, `modkit`, `framework-comparison`, `api-contract`, `docker-orchestration`, `quality-gates` |
| **Homepage** | `https://github.com/go-modkit/benchmarks` |

## Application Checklist

### Automated (via GitHub CLI)

If you have the `gh` CLI installed and authenticated, run the following command to apply the profile:

```bash
gh repo edit go-modkit/benchmarks \
  --description "Parity-gated benchmark harness for API framework performance comparison. Ensures correctness via declarative contract fixtures before measuring throughput and latency." \
  --add-topic "go,benchmark,api-parity,performance-testing,reproducibility,modkit,framework-comparison,api-contract,docker-orchestration,quality-gates" \
  --homepage "https://github.com/go-modkit/benchmarks"
```

### Manual Fallback

If the GitHub CLI is unavailable, follow these steps:

1. Navigate to the repository on GitHub: [go-modkit/benchmarks](https://github.com/go-modkit/benchmarks)
2. Click on the **Settings** gear icon (or the "About" section edit icon on the main page).
3. In the **Description** field, paste:
   > Parity-gated benchmark harness for API framework performance comparison. Ensures correctness via declarative contract fixtures before measuring throughput and latency.
4. In the **Website** field, paste:
   > https://github.com/go-modkit/benchmarks
5. In the **Topics** section, add the following tags one by one:
   - `go`
   - `benchmark`
   - `api-parity`
   - `performance-testing`
   - `reproducibility`
   - `modkit`
   - `framework-comparison`
   - `api-contract`
   - `docker-orchestration`
   - `quality-gates`
6. Click **Save changes**.

## Verification

To verify the current metadata, run:

```bash
gh repo view go-modkit/benchmarks --json description,repositoryTopics,homepage
```
