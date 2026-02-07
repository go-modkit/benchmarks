# Shell Integration Tests

This directory contains `bats` tests for benchmark orchestration shell scripts.

Run locally:

```bash
bats tests/integration
```

These tests are intended to validate argument guards and path safety checks without
requiring Docker or live framework services.
