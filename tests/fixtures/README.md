# Test Fixtures for Benchmark Scripts

This directory contains deterministic test fixtures for validating the benchmark pipeline.

## Structure

```
tests/fixtures/
├── raw/           # Raw benchmark result JSON files
├── summary/       # Expected summary.json outputs
└── compose/       # Docker compose test files
```

## Fixture Categories

### Raw Results
- `ok/` - Successful benchmark runs with full metrics
- `skipped/` - Skipped runs (health unavailable, parity failed, etc.)
- `invalid/` - Malformed JSON for error testing

### Usage
Fixtures are loaded by test files to verify:
1. Schema validation behavior
2. Report generation output
3. Quality check calculations
4. Edge case handling

## Creating New Fixtures

When adding fixtures:
1. Use realistic but anonymized data
2. Include both happy path and edge cases
3. Document any special conditions in comments
4. Keep fixtures minimal - only include required fields
