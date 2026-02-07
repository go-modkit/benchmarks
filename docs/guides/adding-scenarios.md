# Adding Parity Scenarios

## 1) Pick the fixture file

Group by endpoint domain:

- `health.json`
- `users-create.json`
- `users-read.json`
- `users-update.json`
- `users-delete.json`

If needed, add a new endpoint-grouped file under `test/fixtures/parity/scenarios/`.

## 2) Add scenario entries

Add a JSON object with:

- unique `name`
- minimal `request`
- explicit expected `response`

Prefer deterministic expectations. Use matcher tokens only for dynamic fields.

## 3) Update seed state if required

If the scenario depends on baseline data, update `test/fixtures/parity/seed.json`.

## 4) Run locally

```bash
PARITY_TARGET=http://localhost:3001 make parity-check
```

## 5) Review checklist

- scenario name is descriptive
- endpoint-grouped file organization preserved
- no implementation-specific assumptions leaked into contract
- docs/design updated if contract semantics changed
