# Methodology

## Fair Comparison
- Identical endpoints and response formats
- SQLite in-memory for all frameworks
- Same load test parameters

## Environment
- Docker + Docker Compose
- wrk
- Python 3

## Benchmark Parameters
- wrk: -t12 -c400 -d30s
- Warmup: 1000 requests

## Notes
This is a stub. Expand with hardware/versions and interpretation guidance.
