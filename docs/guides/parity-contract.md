# Parity Contract Guide

## Contract location

- fixtures: `test/fixtures/parity/`
- design intent: `docs/design/002-api-parity-contract.md`

## Fixture format

Each scenario file is a JSON array:

```json
[
  {
    "name": "scenario name",
    "request": {"method": "GET", "path": "/health"},
    "response": {"status": 200, "body": {"status": "ok"}}
  }
]
```

## Request block

- `method` (optional; defaults to `GET`)
- `path` (required)
- `headers` (optional)
- `body` (optional)

## Response block

- `status` (required, exact)
- `headers` (optional, expected headers must exist)
- `body` (optional, recursive comparison)

## Matchers

- `@any_number`
- `@is_iso8601`

Both can be full values or embedded in strings.

## Change policy

- changing matcher semantics requires:
  - parity runner updates
  - fixture updates
  - design doc update
